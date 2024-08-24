"""Read all files and put into CODE.md"""

from glob import glob

for file in glob("model_view_controller/*", recursive=True):
    with open(file, "r") as read_f:
        with open("CODE.md", "a") as write_f:
            write_f.write(f"# {file}\n\n```")
            write_f.write(read_f.read())
            write_f.write("```\n\n")

for file in glob("mvc_customer/*", recursive=True):
    with open(file, "r") as read_f:
        with open("CODE.md", "a") as write_f:
            write_f.write(f"# {file}\n\n```")
            write_f.write(read_f.read())
            write_f.write("```\n\n")
