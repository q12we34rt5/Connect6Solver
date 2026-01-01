import time
from .node import SGFNode, BaseSGFNode
from .exceptions import SGFError
from . import DynamicLibrary as dl
from .utils import Timer, DummyTimer, TrackingTimer
from .parser import T, NodeAllocator, DefaultNodeAllocator
import numpy as np
import itertools
import os
import sys
import typing
import threading


base_dir = os.path.dirname(os.path.abspath(__file__))
lib = dl.DynamicLibrary(extra_compile_flags=['-I' + base_dir])
lib.compile_string(
    r'''
#include "parser.hpp"
#include <cstring>

struct ParserObject {
    SGFParser* parser;
    TrackingNodeAllocator<StringSGFNode>* allocator;
    StringSGFNode* root;
};

API ParserObject* create_parser(const char* sgf, size_t start, void (*progress_callback)(int, int)) {
    ParserObject* obj = new ParserObject();
    obj->allocator = new TrackingNodeAllocator<StringSGFNode>();
    obj->parser = new SGFParser(sgf, *obj->allocator, start, progress_callback);
    return obj;
}

API void delete_parser(ParserObject* obj) {
    obj->allocator->deallocateAll();
    delete obj->parser;
    delete obj->allocator;
    delete obj;
}

API void parse(ParserObject* obj) {
    obj->root = static_cast<StringSGFNode*>(obj->parser->next_node());
    while (obj->parser->next_node() != nullptr);
}

API size_t calculate_tag_value_string_size(ParserObject* obj) {
    size_t total = 0;
    for (auto& node : obj->allocator->getAllocatedNodes()) {
        total += node->content.size();
    }
    return total;
}

API size_t calculate_num_tag_value(ParserObject* obj) {
    size_t total = 0;
    for (auto& node : obj->allocator->getAllocatedNodes()) {
        total += node->tag_value_sizes.size();
    }
    return total;
}

API size_t calculate_num_nodes(ParserObject* obj) {
    return obj->allocator->getAllocatedNodes().size();
}

/**
 * Convert the tree structure into a compact representation using depth-first traversal.
 *
 * @param obj The parser object containing the tree structure and relevant metadata.
 * @param tag_value_string A single continuous string that holds all tag and value pairs in depth-first order.
 *                         The string is split based on the sizes provided in `tag_value_sizes`.
 *                         Size: `calculate_tag_value_string_size(obj)` returns the total size of this string.
 * @param tag_value_sizes An array of sizes corresponding to each tag or value in `tag_value_string`,
 *                        allowing correct splitting of the string into individual tags and values.
 *                        Size: `calculate_num_tag_value(obj)` returns the total number of tags and values.
 * @param is_tag A boolean (char) array indicating whether each segment in `tag_value_string` is a tag (true) or a value (false).
 *               This helps differentiate between property names and their associated values.
 *               Size: Same as `tag_value_sizes`.
 * @param tag_value_count An array that specifies how many tag-value pairs each node contains. This array helps in
 *                        reconstructing the tree structure from the linearized tag-value pairs.
 *                        Size: `calculate_num_nodes(obj)` returns the total number of nodes.
 * @param parent_indices An array that stores the parent index for each node during depth-first traversal.
 *                       The root node will have a parent index of `-1`. Size: `calculate_num_nodes(obj)`.
 */
API void serialize_tree(ParserObject* obj, char* tag_value_string, size_t tag_value_sizes[], char is_tag[], size_t tag_value_count[], size_t parent_indices[]) {
    // Use depth-first search (DFS) to convert the tree structure into a compact representation
    size_t offset = 0;
    size_t tag_value_index = 0;
    size_t node_index = 0;
    std::function<void(StringSGFNode*, size_t)> dfs = [&](StringSGFNode* node, size_t parent_index) {
        // Serialize the tag-value pairs of the current node
        strcpy(tag_value_string + offset, node->content.c_str());  // node->content is a string that holds all tag-value pairs
        offset += node->content.size();

        // Serialize the tag-value sizes and is_tag array
        // assert(node->tag_value_sizes.size() == node->is_tag.size());
        for (size_t i = 0; i < node->tag_value_sizes.size(); i++) {
            tag_value_sizes[tag_value_index] = node->tag_value_sizes[i];
            is_tag[tag_value_index] = node->is_tag[i];
            tag_value_index++;
        }

        // Serialize the node tag count and parent indices
        size_t current_node_index = node_index++;
        tag_value_count[current_node_index] = node->tag_value_sizes.size();
        parent_indices[current_node_index] = parent_index;

        auto child = static_cast<StringSGFNode*>(node->child);
        while (child != nullptr) {
            dfs(child, current_node_index);
            child = static_cast<StringSGFNode*>(child->next_sibling);
        }
    };
    dfs(obj->root, -1);
}
''', functions={
        'create_parser': {'argtypes': [dl.char_p, dl.uint64, dl.void_p], 'restype': dl.void_p},
        'delete_parser': {'argtypes': [dl.void_p], 'restype': dl.void},
        'parse': {'argtypes': [dl.void_p], 'restype': dl.void},
        'calculate_tag_value_string_size': {'argtypes': [dl.void_p], 'restype': dl.uint64},
        'calculate_num_tag_value': {'argtypes': [dl.void_p], 'restype': dl.uint64},
        'calculate_num_nodes': {'argtypes': [dl.void_p], 'restype': dl.uint64},
        'serialize_tree': {'argtypes': [dl.void_p, dl.int8_p, dl.npint64arr, dl.npint8arr, dl.npint64arr, dl.npint64arr], 'restype': dl.void},
    })


class AllocateOnlyNodePool(typing.Generic[T]):
    def __init__(self, size: int, node_allocator: NodeAllocator[T]):
        self.size = size
        self.node_allocator = node_allocator
        self.nodes: typing.List[typing.Optional[T]] = [node_allocator.allocate() for _ in range(size)]
        self.index = 0

    def allocate(self) -> T:
        if self.index >= self.size:  # No more nodes available
            return self.node_allocator.allocate()
        node = self.nodes[self.index]
        self.nodes[self.index] = None
        self.index += 1
        assert node is not None
        return node


class SGFParser(typing.Generic[T]):
    def __init__(self, node_allocator: NodeAllocator[T] = DefaultNodeAllocator()):
        self.node_allocator = node_allocator
        self.node_pool: typing.Optional[AllocateOnlyNodePool[T]] = None
        self.node_pool_thread: typing.Optional[threading.Thread] = None

    def parse(self, sgf: str, start: int = 0, show_progress: bool = False) -> T:
        start_time: typing.Optional[float] = None
        if show_progress:
            start_time = time.time()

        # Estimate the number of nodes in the SGF file and create a node pool
        self.node_pool = None

        def create_node_pool() -> None:
            nonlocal sgf
            estimated_size = sgf.count(';')
            self.node_pool = AllocateOnlyNodePool(
                estimated_size, self.node_allocator)
        self.node_pool_thread = threading.Thread(target=create_node_pool)
        self.node_pool_thread.start()

        # Call the C++ parser
        tag_value_string, tag_value_sizes, is_tag, tag_value_count, parent_indices = self._parse(
            sgf, start, show_progress)

        # Construct the tree structure from the serialized data
        root = self._construct_tree(
            tag_value_string, tag_value_sizes, is_tag, tag_value_count, parent_indices, show_progress)

        if show_progress and start_time is not None:
            end_time = time.time()
            print(
                f"| Total time: {end_time - start_time:.2f}s", file=sys.stderr)
        return root

    def _parse(self, sgf: str, start: int = 0, show_progress: bool = False) -> typing.Tuple[bytearray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        Progress = DummyTimer if not show_progress else Timer

        # Create the parser object
        with Progress("[1/7] Creating parser...", end="\r"):
            parser = lib.create_parser(sgf.encode(), start, None)  # type: ignore[attr-defined]

        # Parse the SGF string
        with Progress("[2/7] Parsing SGF...", end="\r"):
            lib.parse(parser)  # type: ignore[attr-defined]

        # Calculate the sizes of the tag-value string and the number of tag-value pairs
        with Progress("[3/7] Fetching tree metadata...", end="\r"):
            tag_value_string_size = lib.calculate_tag_value_string_size(parser)  # type: ignore[attr-defined]
            num_tag_value = lib.calculate_num_tag_value(parser)  # type: ignore[attr-defined]
            num_nodes = lib.calculate_num_nodes(parser)  # type: ignore[attr-defined]

        # Serialize the tree structure into a compact representation
        with Progress("[4/7] Serializing tree...", end="\r"):
            tag_value_string = bytearray(tag_value_string_size)
            tag_value_sizes = np.zeros(num_tag_value + 1, dtype=np.int64)
            is_tag = np.zeros(num_tag_value, dtype=np.int8)
            tag_value_count = np.zeros(num_nodes + 1, dtype=np.int64)
            parent_indices = np.zeros(num_nodes, dtype=np.int64)
            lib.serialize_tree(  # type: ignore[attr-defined]
                parser, tag_value_string, tag_value_sizes[1:], is_tag, tag_value_count[1:], parent_indices)

        # Delete the parser object
        with Progress("[5/7] Deleting parser...", end="\r"):
            lib.delete_parser(parser)  # type: ignore[attr-defined]

        return tag_value_string, tag_value_sizes, is_tag, tag_value_count, parent_indices

    def _construct_tree(
            self,
            tag_value_string: bytearray,
            tag_value_sizes: np.ndarray,
            is_tag: np.ndarray,
            tag_value_count: np.ndarray,
            parent_indices: np.ndarray,
            show_progress: bool = False) -> T:
        Progress = DummyTimer if not show_progress else Timer
        TrackProgress = DummyTimer if not show_progress else TrackingTimer

        with Progress("[6/7] Preparing node data...", end="\r"):
            tag_value_string_decoded = tag_value_string.decode()
            tag_value_list = [tag_value_string_decoded[s:e] for s, e in zip(itertools.accumulate(
                tag_value_sizes), itertools.accumulate(tag_value_sizes[1:]))]

        # Construct the tree structure
        with TrackProgress("[7/7] Constructing tree...", len(parent_indices), end=" ") as progress:
            # with Progress("[7/7] Constructing tree...", end=" "):
            nodes: typing.List[typing.Optional[T]] = [None] * len(parent_indices)
            node_tag_value_indices = zip(itertools.accumulate(
                tag_value_count), itertools.accumulate(tag_value_count[1:]))

            # Wait for the node pool to be created
            assert self.node_pool_thread is not None
            self.node_pool_thread.join()
            assert self.node_pool is not None

            for i, ((s, e), parent_index) in enumerate(zip(node_tag_value_indices, parent_indices)):
                node = self.node_pool.allocate()
                nodes[i] = node

                # Parse the tag-value pairs for the current node
                tag = None
                values = []
                for j in range(s, e):
                    if is_tag[j]:
                        if tag is not None:
                            node[tag] = values
                            values = []
                        tag = tag_value_list[j]
                    else:
                        values.append(tag_value_list[j])
                if tag is not None:
                    node[tag] = values

                # Add the current node to its parent
                if parent_index >= 0:
                    parent = nodes[parent_index]
                    parent.add_child(node)

                # Update progress
                progress.update(i + 1)

        root = nodes[0]
        assert root is not None
        return root
