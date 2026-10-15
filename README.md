# timer
A small python timer; built because I needed a very simple timer instead of the ones available.

# To create the .exe file;

Download the two files to a folder on your computer.

Open in VS Code.

Open a terminal; double check that you have pyinstaller already installed:

python -m PyInstaller --version
(if you don't have it, install it)

Then run the following:
python -m PyInstaller --onefile --windowed timer.py

This will generate your .exe file in the folder you placed the files in (usually in dist folder).



