#pragma once

#include "exceptions.hpp"
#include "lexer.hpp"
#include <stack>
#include <stdexcept>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

class BaseSGFNode {
public:
    BaseSGFNode() : parent(nullptr), child(nullptr), next_sibling(nullptr), num_children(0) {}
    virtual ~BaseSGFNode() = default;

    virtual void addChild(BaseSGFNode* node)
    {
        node->detach();
        if (child == nullptr) {
            child = node;
        } else {
            BaseSGFNode* current = child;
            while (current->next_sibling != nullptr) {
                current = current->next_sibling;
            }
            current->next_sibling = node;
        }
        node->parent = this;
        ++num_children;
    }

    virtual BaseSGFNode* detach()
    {
        if (parent != nullptr) {
            if (parent->child == this) {
                parent->child = next_sibling;
            } else {
                BaseSGFNode* ptr = parent->child;
                while (ptr->next_sibling != this) {
                    ptr = ptr->next_sibling;
                }
                ptr->next_sibling = next_sibling;
            }
            --parent->num_children;
            parent = nullptr;
            next_sibling = nullptr;
        }
        return this;
    }

    virtual void addProperty(const std::string& tag, const std::vector<std::string>& values) = 0;

public:
    BaseSGFNode* parent;
    BaseSGFNode* child;
    BaseSGFNode* next_sibling;
    int num_children;
};

class StringSGFNode : public BaseSGFNode {
public:
    StringSGFNode() : BaseSGFNode() {}

    void addProperty(const std::string& tag, const std::vector<std::string>& values) override
    {
        content += tag;
        tag_value_sizes.push_back(tag.size());
        is_tag.push_back(true);
        for (const std::string& value : values) {
            content += value;
            tag_value_sizes.push_back(value.size());
            is_tag.push_back(false);
        }
    }

    std::string content;
    std::vector<size_t> tag_value_sizes;
    std::vector<bool> is_tag;
};

class BaseNodeAllocator {
public:
    virtual BaseSGFNode* allocate() = 0;

    virtual void deallocate(BaseSGFNode* node) = 0;
};

template <typename NodeType>
class NodeAllocator : public BaseNodeAllocator {
public:
    BaseSGFNode* allocate() override
    {
        return new NodeType();
    }

    void deallocate(BaseSGFNode* node) override
    {
        delete static_cast<NodeType*>(node);
    }
};

template <typename NodeType>
class TrackingNodeAllocator : public BaseNodeAllocator {
public:
    BaseSGFNode* allocate() override
    {
        NodeType* node = new NodeType();
        allocated_nodes.insert(node);
        return node;
    }

    void deallocate(BaseSGFNode* node) override
    {
        if (allocated_nodes.erase(static_cast<NodeType*>(node)) > 0) {
            delete node;
        }
    }

    const std::unordered_set<NodeType*>& getAllocatedNodes() const
    {
        return allocated_nodes;
    }

    void deallocateAll()
    {
        for (NodeType* node : allocated_nodes) {
            delete node;
        }
        allocated_nodes.clear();
    }

private:
    std::unordered_set<NodeType*> allocated_nodes;
};

class SGFParser {
    class DummyNode : public BaseSGFNode {
    public:
        DummyNode() : BaseSGFNode() {}

        void addChild(BaseSGFNode* node) override
        {
            if (child != nullptr) {
                throw std::runtime_error("DummyNode can only have one child");
            }
            child = node;
        }

        void addProperty(const std::string& tag, const std::vector<std::string>& values) override
        {
            throw std::runtime_error("DummyNode cannot have properties");
        }
    };

    struct Element {
        enum class Type {
            LEFT_PAREN,
            NODE,
        } type;
        size_t start;
        size_t end;
        BaseSGFNode* node;
    };

public:
    SGFParser(std::string sgf, BaseNodeAllocator& allocator, size_t start = 0, std::function<void(int, int)> progress_callback = nullptr)
        : lexer(std::move(sgf), start, std::move(progress_callback)), allocator(allocator), root(new DummyNode()), current(root)
    {
        next_can_be_left_paren = true;
        next_can_be_right_paren = false;
        next_can_be_semicolon = false;
        next_can_be_tag = false;
        next_can_be_value = false;
    }

    ~SGFParser()
    {
        delete root;
    }

    BaseSGFNode* next_node()
    {
        auto cache_tag = std::string();
        auto cache_values = std::vector<std::string>();
        // bool has_value = false;

        while (true) {
            const SGFToken& token = lexer.next_token();
            if (token.type == SGFTokenType::ENDOFFILE) {
                break;
            }
            switch (token.type) {
                case SGFTokenType::LEFT_PAREN: {
                    if (!next_can_be_left_paren) {
                        throw SGFError("Unexpected left parentheses", token.start, token.end);
                    }

                    stack.push({Element::Type::NODE, 0, 0, current});
                    stack.push({Element::Type::LEFT_PAREN, token.start, token.end, nullptr}); // append '(' token to stack

                    // update states
                    next_can_be_left_paren = false;
                    next_can_be_right_paren = false;
                    next_can_be_semicolon = true;
                    next_can_be_tag = false;
                    next_can_be_value = false;
                    break;
                }
                case SGFTokenType::RIGHT_PAREN: {
                    if (!next_can_be_right_paren) {
                        throw SGFError("Unexpected right parentheses", token.start, token.end);
                    }

                    if (stack.empty()) {
                        throw SGFError("Unmatched right parentheses", token.start, token.end);
                    }

                    // store tag and value to current node if needed
                    BaseSGFNode* return_node = nullptr;
                    if (!cache_values.empty()) {
                        // if (has_value) {
                        current->addProperty(cache_tag, cache_values);
                        // current->setContent(content);
                        cache_values.clear(); // not needed because the cache will be released after the node is returned
                        // has_value = false;
                        return_node = current;
                    }

                    // pop until '('
                    while (true) {
                        if (stack.empty()) {
                            throw SGFError("Unmatched right parentheses", token.start, token.end);
                        }
                        if (stack.top().type == Element::Type::LEFT_PAREN) {
                            stack.pop(); // pop '(' token
                            break;
                        }
                        stack.pop(); // pop node
                    }
                    current = stack.top().node; // pop the node before '('
                    stack.pop();

                    // update states
                    next_can_be_left_paren = true;
                    next_can_be_right_paren = true;
                    next_can_be_semicolon = false;
                    next_can_be_tag = false;
                    next_can_be_value = false;

                    // return the node if needed
                    if (return_node != nullptr) {
                        return return_node;
                    }
                    break;
                }
                case SGFTokenType::SEMICOLON: {
                    if (!next_can_be_semicolon) {
                        throw SGFError("Unexpected semicolon", token.start, token.end);
                    }

                    // store tag and value to current node if needed
                    BaseSGFNode* return_node = nullptr;
                    if (!cache_values.empty()) {
                        // if (has_value) {
                        current->addProperty(cache_tag, cache_values);
                        // current->setContent(content);
                        // cache_values.clear();  // not needed because the cache will be released after the node is returned
                        // has_value = false;
                        return_node = current;
                    }

                    // create a new node
                    stack.push({Element::Type::NODE, 0, 0, current});
                    current = allocator.allocate();
                    stack.top().node->addChild(current);
                    // content = token.value;  // begin the content of the new node (';')

                    // update states
                    next_can_be_left_paren = false;
                    next_can_be_right_paren = false;
                    next_can_be_semicolon = false;
                    next_can_be_tag = true;
                    next_can_be_value = false;

                    // return the node if needed
                    if (return_node != nullptr) {
                        return return_node;
                    }
                    break;
                }
                case SGFTokenType::TAG: {
                    if (!next_can_be_tag) {
                        throw SGFError("Unexpected tag " + token.value, token.start, token.end);
                    }

                    // store tag and value to current node if needed
                    if (!cache_values.empty()) {
                        current->addProperty(cache_tag, cache_values);
                        cache_values.clear();
                    }
                    // has_value = false;

                    cache_tag = token.value; // cache the tag, will be used when the value comes
                    // content += token.value;  // append the tag to the content

                    // update states
                    next_can_be_left_paren = false;
                    next_can_be_right_paren = false;
                    next_can_be_semicolon = false;
                    next_can_be_tag = false;
                    next_can_be_value = true;
                    break;
                }
                case SGFTokenType::VALUE: {
                    if (!next_can_be_value) {
                        throw SGFError("Unexpected value " + token.value, token.start, token.end);
                    }

                    cache_values.push_back(token.value);
                    // has_value = true;
                    // // append the value to the content
                    // content += '[';
                    // content += token.value;
                    // content += ']';

                    // update states
                    next_can_be_left_paren = true;
                    next_can_be_right_paren = true;
                    next_can_be_semicolon = true;
                    next_can_be_tag = true;
                    next_can_be_value = true;
                    break;
                }
                case SGFTokenType::IGNORE:
                    break;
                default:
                    throw SGFError("Unexpected token " + token.value, token.start, token.end);
                    break;
            }
        }

        // make sure all the parentheses are matched
        if (!stack.empty()) {
            // pop until the first '(' token
            Element last_left_paren;
            while (!stack.empty()) {
                if (stack.top().type == Element::Type::LEFT_PAREN) {
                    last_left_paren = stack.top();
                    stack.pop();
                    break;
                }
                stack.pop();
            }
            throw SGFError("Unmatched left parentheses", last_left_paren.start, last_left_paren.end);
        }

        // remove the dummy root
        BaseSGFNode* root_child = root->child;
        if (root_child != nullptr) {
            root_child->detach();
        }

        return nullptr;
    }

private:
    SGFLexer lexer;
    BaseNodeAllocator& allocator;
    std::stack<Element> stack;
    BaseSGFNode* root;
    BaseSGFNode* current;
    // std::string content;  // content of the current node

    bool next_can_be_left_paren;
    bool next_can_be_right_paren;
    bool next_can_be_semicolon;
    bool next_can_be_tag;
    bool next_can_be_value;
};
