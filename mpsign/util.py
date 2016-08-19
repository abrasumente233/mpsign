
# Make a decision between several packages
# Which priority is up to the sort of the given packages
def select_package(packages):
    for package in packages:
        try:
            __import__(package)
            return package
        except:
            # No matter whatever the error is
            pass

    return None  # No avilable package detected
