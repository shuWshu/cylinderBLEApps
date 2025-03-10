from scrollTask_cylinderNew import App_cylinder
from scrollTask_iphone import App_iphone

# -----パラメータ-----
ID = 0
DIST = 0
#MODE = "iphone"
MODE = "cylinder"
# -----パラメータ-----

def main():
    if MODE == "iphone":
        app = App_iphone(ID, DIST, MODE)
    elif MODE == "cylinder":
        app = App_cylinder(ID, DIST, MODE)
    else:
        return
    app.run()

if __name__ == "__main__":
    main()