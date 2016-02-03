from BingAutomater import PCSearcher, MobileSearcher


def main():
    pc_driver = PCSearcher()
    mobile_driver = MobileSearcher()

    pc_driver.set_algorithm('research')
    mobile_driver.set_algorithm('research')


    pc_driver.start()
    mobile_driver.start()

    while True:
        if not pc_driver.is_active and mobile_driver.is_active():
            break
        if pc_driver.is_active():
            pc_driver.search()
        if mobile_driver.is_active():
            mobile_driver.search()



if __name__ == '__main__':
    main()
