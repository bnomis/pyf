# this is so coverage will work across processes
try:
    import coverage
    coverage.process_startup()
except:
    pass

