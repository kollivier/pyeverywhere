import logging
import subprocess


def osx_code_sign_file(filename, identity):
    cmd_base = ["codesign", "--force", "-vvv", "--verbose=4", "--sign", identity]

    cmd = list(cmd_base)
    cmd.append(filename)
    logging.info("running %s" % " ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    for line in proc.stdout:
        logging.info(line)
    for line in proc.stderr:
        logging.error(line)

    if proc.returncode != 0:
        logging.error("Code signing failed for %s" % filename)
        return False
    else:
        cmd = ['codesign', "--verify", "--deep", "--verbose=4", filename]
        logging.info("verifying signature")
        if subprocess.call(cmd) != 0:
            logging.info("signature verification failed")
            logging.info("Command is %s" % " ".join(cmd))
            return False

    logging.info("Code signing succeeded for %s" % filename)
    return True
