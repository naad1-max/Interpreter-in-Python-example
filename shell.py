from interp import run

while True:
    to_run = input(">>> ")

    if to_run != "exit":
        run(to_run)
    
    else:
        break

