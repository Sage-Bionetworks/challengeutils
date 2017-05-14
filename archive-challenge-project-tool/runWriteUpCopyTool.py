import signal
import time
import os
import subprocess

class GracefulKiller:
    kill_now = False
    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self,signum, frame):
        self.kill_now = True

if __name__ == '__main__':
    killer = GracefulKiller()
    while True:
        synUser = os.environ['SYNAPSE_USERNAME']
        synPass = os.environ['SYNAPSE_PASSWORD']
        chalName = os.environ['CHALLENGE_NAME']

        validateSub = ['python','challenge.py','--challengeName',chalName,'-u',synUser,'-p',synPass,'--send-messages','--notifications','--acknowledge-receipt','validate','9603284','--admin','3336298']
        archiveSub = ['python','challenge.py','--challengeName',chalName,'-u',synUser,'-p',synPass,'--notifications','archive','9603284']

        subprocess.call(validateSub, stderr=subprocess.STDOUT)
        subprocess.call(archiveSub, stderr=subprocess.STDOUT)

        time.sleep(43200)
        if killer.kill_now:
            break
    print("End of the program. I was killed gracefully :)")