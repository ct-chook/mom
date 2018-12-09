from src.handlers import mom_handler


class MasterOfMonsters:
    def __init__(self):
        master = mom_handler.MomHandler()
        master.start()


print("Starting")
MasterOfMonsters()
print("Bye")
