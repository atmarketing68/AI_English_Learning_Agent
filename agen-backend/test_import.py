import traceback
try:
    import app.main
    print("Success!")
except Exception as e:
    traceback.print_exc()
