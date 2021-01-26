#!/usr/bin/env python

from win32com.client import selecttlb

items = selecttlb.EnumTlbs()

def getDescsFromTlb():
	return list(map((lambda x: x.desc), items))

print('Enter a part of string you want to search in description of dll items: ')
search_string = input(': ')

if not search_string:
        print('Nothing entered')
else:        
        all_descriptions = getDescsFromTlb()

        for desc in all_descriptions:
                if search_string.lower() in desc.lower():
                        print(desc)

input('Press any key to quit')
