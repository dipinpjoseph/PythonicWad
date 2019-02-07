from xlrd import open_workbook

def ifsc_excel_reader():
    ifsc_details = []
    wb = open_workbook('IFCB2009_77.xlsx')
    for sheet in wb.sheets():
        for each_row in range(1,sheet.nrows):
            each_branch = {}
            each_branch["Bank Name"] = str(sheet.cell(each_row,0).value)
            each_branch["IFSC Code"] = str(sheet.cell(each_row,1).value)
            each_branch["MICR Code"] = str(sheet.cell(each_row,2).value)[:-2]
            each_branch["Bank Branch"] = str(sheet.cell(each_row,3).value)
            each_branch["Bank Address"] = str(sheet.cell(each_row,4).value)
            each_branch["Contact"] = str(sheet.cell(each_row,5).value)[:-2]
            each_branch["City"] = str(sheet.cell(each_row,6).value)
            each_branch["District"] = str(sheet.cell(each_row,7).value)
            each_branch["State"] = str(sheet.cell(each_row,8).value)
            each_branch["Branch Code"] = str(sheet.cell(each_row,1).value[-6:])
            ifsc_details.append(each_branch)
    return ifsc_details
    #print (ifsc_details)
#ifsc_excel_reader()

