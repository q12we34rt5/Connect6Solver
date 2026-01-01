import subprocess
import os


def main():
    # Define the working directory where the executable is located
    # This is important to ensure the NCTU6 (exec) program runs correctly
    working_dir = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "NCTU6")

    command = [
        "./exec",
        "-playtsumego", ";B[JJ];W[LH];W[HH];B[JI];B[KJ]",
        "-ignore", ";W[IH];W[JH]"
    ]

    print(f"Executing command in {working_dir}: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            cwd=working_dir,
            capture_output=True,
            text=True
        )

        if result.stdout:
            print("Output:")
            print(result.stdout)

        if result.stderr:
            print("Error Output:")
            print(result.stderr)

        if result.returncode != 0:
            print(f"Command finished with error code: {result.returncode}")

    except FileNotFoundError:
        print(
            f"Error: Could not find the executable or directory. Checked in: {working_dir}")
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
