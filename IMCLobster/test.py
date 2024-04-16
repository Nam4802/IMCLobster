shell = {'pizza': 1.41, 'wasabi': 0.61, 'snow': 2.08}
pizza = {'shell': 0.71, 'wasabi': 0.48, 'snow': 1.52}
wasabi = {'shell': 1.56, 'pizza': 2.05, 'snow': 3.26}
snow = {'shell': 0.46, 'pizza': 0.64, 'wasabi': 0.3}

allprod = {'shell':shell, 'pizza':pizza, 'wasabi':wasabi, 'snow':snow}
i = 0

for prod1, rate1 in allprod['shell'].items():

    for prod2, rate2 in allprod[prod1].items():

        #total = rate1 * rate2
        #if total >= 1 and prod2 == 'shell':
        #     print(total)
        #     print('shell ' + prod1 + ' ' + prod2)

        for prod3, rate3 in allprod[prod2].items():

            total = rate1 * rate2 * rate3
            if total >= 1 and prod3 == 'shell':
                 print(total)
                 print('shell ' + prod1 + ' ' + prod2 + ' ' + prod3)

            #for prod4, rate4 in allprod[prod3].items():

            #    total = rate1 * rate2 * rate3 * rate4
            #    if total >= 1 and prod4 == 'shell':
            #        print(total)
            #        print('shell ' + prod1 + ' ' + prod2 + ' ' + prod3 + ' ' + prod4)

                #for prod5, rate5 in allprod[prod4].items():

                #    total = rate1 * rate2 * rate3 * rate4 * rate5
                #    if total >= 1 and total <= 2 and prod5 == 'shell':
                #        print(total)
                #        print('shell ' + prod1 + ' ' + prod2 + ' ' + prod3 + ' ' + prod4 + ' ' + prod5)