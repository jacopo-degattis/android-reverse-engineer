#!/usr/bin/env python3

import sys
import stat
import zipfile
import requests
from shutil import which, rmtree
from os import remove, system, path, access, X_OK, chmod, listdir

GENERATE_CERT = "keytool -genkey -v -keystore cert.keystore -alias alias_name -keyalg RSA -keysize 2048 -validity 10000"
SIGN_APK = "jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore {keystore} {apk} {alias}"

def exists(name: str) -> bool:
    return which(name)

def cleanup() -> None:
    blacklist = ["README.md", "toolkit.py"]
    for entry in filter(lambda x: x not in blacklist, listdir("./")):
        rmtree(entry) if path.isdir(entry) else remove(entry)

# Fetch tools 
# TODO: add local file checking
def install(name: str) -> None:

    installers = {
        "apktool": [
            "https://raw.githubusercontent.com/iBotPeaches/Apktool/master/scripts/linux/apktool",
            "https://bitbucket.org/iBotPeaches/apktool/downloads/apktool_2.6.1.jar"
        ],
        "enjarify": [ "https://github.com/google/enjarify/archive/refs/tags/1.0.3.zip" ]
    }

    for step in installers[name]:
        res = requests.get(step)

        if not res.status_code == 200:
            print(f"[-] Failed downloading resource {step}")
            return

        filename: str = step.split("/")[-1]

        with open(filename, "wb") as output_file:
            output_file.write(res.content)

        if filename.split(".")[-1] == "zip":
            # Unzip the file
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                res = zip_ref.extractall(f"./")
                system(f"mv {zip_ref.infolist()[0].filename} {name}")

            remove(filename)

def help() -> None:
    print("""
Toolkit v0.0.1

usage: toolkit.py
    decompile <input_apk>   Decompile APK file
    rebuild <input_folder> Rebuild APK from smali folder and sign with keystore
    """)

def is_executable(filename: str) -> bool:
    return access(filename, X_OK)

def apktool(action, filename) -> int:
    return system(f"apktool {action} {filename}")

def sign_apk(filename: str) -> None:
    print("Got => ", filename)
    return system(SIGN_APK.format(keystore="cert.keystore", apk=f"{filename}.apk", alias="alias_name"))

def rebuild(*args):
    res = apktool("b", *args)

    if not res == 0:
        return "Error while building apk"

    if not path.isfile("cert.keystore"):
        system(GENERATE_CERT)

    return sign_apk(args[0])

# TODO: not working, path is wrong
def enjarify(filename: str) -> None:
    if not is_executable("./enjarify/enjarify.sh"):
        system("chmod +x ./enjarify/enjarify.sh")        

    return system(f"./enjarify/enjarify.sh {filename}")

def dispatch(command: str, *args) -> None:
    if command == "decompile":
        return apktool("d", *args)
    elif command == "rebuild":
        return rebuild(*args)
    elif command == "enjarify":
        return enjarify(*args)

    return -1

if __name__ == "__main__":
    # What about android sdk ?

    tools: [str] = ["apktool", "enjarify"]

    # Check for existing tools
    for tool in tools: install(tool) if not exists(tool) else None

    if len(sys.argv) < 1:
        help()
        exit(0)

    print(len(sys.argv))
    if len(sys.argv) == 2:
        if not sys.argv[1] == "cleanup":
            exit(-1)

        confirm = input("[!] Are you sure you want to delete all file in this directory ? (y/n)")

        if not confirm == "y": exit(0)

        cleanup()


    if len(sys.argv) == 3:
        dispatch(*sys.argv[1:])
    
    exit(0)