from interp import run, Interpreter

while True:
    to_run = input(">>> ")

    if to_run != "exit":
        interp = Interpreter()
        run(to_run, interp)
    
    else:
        break

