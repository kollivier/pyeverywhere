import argparse
import os
import shutil

thisdir = os.path.dirname(os.path.abspath(__file__))

project_name = "PyEverywhere"

parser = argparse.ArgumentParser(description="Create a new %s Project." % project_name)
parser.add_argument('name', help='Name of project to create')
parser.add_argument('--dir', dest='directory', default=os.getcwd(),
                   help='Directory to create the project in. (default: current directory)')

args = parser.parse_args()

if args.name:
    root = os.path.join(args.directory, args.name)
    src_dir = os.path.join(root, "src")
    print("Creating project at %s" % root)
    os.makedirs(src_dir)

    print("Copying mobilepy module to project directory...")
    templates_dir = os.path.join(thisdir, "templates")
    main_script = os.path.join(templates_dir, "AppMain.py")
    android_main = os.path.join(templates_dir, "main.py")
    shutil.copy2(main_script, os.path.join(src_dir, "AppMain.py"))
    shutil.copy2(android_main, os.path.join(src_dir, "main.py"))

    mobile_py = os.path.join(thisdir, "mobilepy")
    shutil.copytree(mobile_py, os.path.join(src_dir, "mobilepy"))

    print("Copying native project files, this make take a little while...")
    native_dir = os.path.abspath(os.path.join(thisdir, "..", "native"))
    shutil.copytree(native_dir, os.path.join(root, "native"))





