import sqlite3
import sys
import os
import json
import rsa
import hashlib
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QTableWidgetItem, QApplication, QWidget, QLabel
from PyQt5.QtGui import QPixmap
import time

class Predlojenia(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Предложения.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.res = []
        self.zagr_pred()
        self.pushButton.clicked.connect(self.prinat)
        self.pushButton_2.clicked.connect(self.otkaz)

    def zagr_pred(self):
        global organization_now, type_organization_now
        table = self.tableWidget
        if type_organization_now == 1:
            table.setColumnCount(13)  # Set three columns
            table.setHorizontalHeaderLabels(["ID", "NumberNakladnoy", "NumberVagon", "Gruzootpravitel",
                                             "Gruzopoluchatel", "Gruzoperevozchik", "Gruz", "VesGruza", "StartStation",
                                             "OverStation", "DateOtpravleniya", "SrokDostavki", "Stoimost"])
            result = self.cur.execute(
                f"""SELECT * FROM Nakladnie WHERE Gruzoperevozchik={organization_now}""").fetchall()
        elif type_organization_now == 4:
            table.setColumnCount(6)  # Set three columns
            table.setHorizontalHeaderLabels(["number_vagona", "type_vagona", "date_start_arenda", "date_end_arenda",
                                             "stoimost", "arendator"])
            vag = self.cur.execute(f"""SELECT Number FROM Vagoni WHERE Vladeles={organization_now}""").fetchall()
            result = []
            for i in vag:
                result += self.cur.execute(f"""SELECT * FROM Arenda WHERE number_vagona={i[0]}""").fetchall()
        else:
            table.setColumnCount(0)  # Set three columns
            result = []
        table.setRowCount(len(result))
        rowPosition = 0
        self.res = result.copy()
        for element in result:
            self.comboBox.addItem(str(rowPosition+1))
            for i in range(len(element)):
                table.setItem(rowPosition, i, QTableWidgetItem(str(element[i])))
            rowPosition += 1

    def prinat(self):
        vibran = int(self.comboBox.currentText())
        itog = self.res[vibran-1]
        b = None
        try:
            block, tranzakt = itog[-1].split('/')
            b = open(f'Blocks/{block}.json')
        except BaseException:
            tranzakt = itog[-1]
        if b is None:
            f = open(f'Tranzactions/{tranzakt}.json')
            f = json.load(f)
        else:
            f = json.load(b)
            f = f['data'][tranzakt]
        tranzaction_creater({
            'hash_of_tranzaktion': f['hash'],
            'sign_of_tranzaktion': f['sign'],
            'sost': 'accepted'
            })
    # доделать itog
    # В процессе создания

    def otkaz(self):
        vibran = int(self.comboBox.currentText())
        itog = self.res[vibran - 1]
        b = None
        try:
            block, tranzakt = itog[-1].split('/')
            b = open(f'Blocks/{block}.json')
        except BaseException:
            tranzakt = itog[-1]
        if b is None:
            f = open(f'Tranzactions/{tranzakt}.json')
            f = json.load(f)
        else:
            f = json.load(b)
            f = f['data'][tranzakt]
        tranzaction_creater({
            'hash_of_tranzaktion': f['hash'],
            'sign_of_tranzaktion': f['sign'],
            'sost': 'denied'
            })


def block_creater(*b):
    bb = list(b).copy()
    bb[0] = tuple(bb[0])
    directory = 'Blocks/'
    files = os.listdir(directory)
    f = open(f'Blocks/{len(files)}.json', 'w')
    f_pre = open(f'Blocks/{len(files)-1}.json')
    f_pre_j = json.load(f_pre)
    block = {
        'index': len(files),
        'time': time.time(),
        'pre_hash': f_pre_j['hash'],
        'data': bb[0],
        'datahash': merkle_tree(b),
        'creator': 'system',
        'nonce': 0
    }
    b1 = json.dumps(block, separators=(',', ':'))
    hashh = hashlib.sha384(b1.encode()).hexdigest()
    while hashh[:4] != '0'*4:
        block['nonce'] += 1
        b1 = json.dumps(block, separators=(',', ':'))
        hashh = hashlib.sha384(b1.encode()).hexdigest()
    block['hash'] = hashh
    block['sign'] = rsa.sign((json.dumps(block, separators=(',', ':'))).encode(), prK, 'SHA-256').hex()
    t1 = json.dumps(block, separators=(',', ':'), indent=4)
    #Доделать подпись
    f.write(t1)
    #В процессе создания


def merkle_tree(tr):
    tr = tr[0]
    for i in range(len(tr)):
        tr[i] = hashlib.sha384(tr[i].encode()).hexdigest()
    k = 0
    while 2**k < len(tr):
        k+=1
    if len(tr) < 2**k:
        tr += [tr[-1] for i in range(2**k-len(tr))]
    for _ in range(k):
        tr_c = []
        for i in range(0, len(tr), 2):
            tr_c.append(hashlib.sha384((tr[i]+tr[i+1]).encode()).hexdigest())
        tr = tr_c.copy()
    return tr[0]


def tranzaction_creater(t):
    directory = 'Tranzactions/'
    files = os.listdir(directory)
    f = open(f'Tranzactions/{len(files)}.json', 'w')
    t['nonce'] = 0
    t1 = json.dumps(t, separators=(',', ':'))
    hashh = hashlib.sha384(t1.encode()).hexdigest()
    while hashh[:4] != '0'*4:
        t['nonce'] += 1
        t1 = json.dumps(t, separators=(',', ':'))
        hashh = hashlib.sha384(t1.encode()).hexdigest()
    t['hash'] = hashh
    t['sign'] = rsa.sign((json.dumps(t, separators=(',', ':'))).encode(), prK, 'SHA-256').hex()
    #Доделать подпись
    t1 = json.dumps(t, separators=(',', ':'), indent=4)
    f.write(t1)
    f.close()
    return len(files)


class Organizasii(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('организация.ui', self)
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.type_id = {}
        self.set_orgTypes()  # Вызываем функцию для заполнения comboBox и заполнения словоря
        self.pushButton.clicked.connect(self.save_results)

    def save_results(self):
        # Получаем все введенные данные
        name_org = str(self.lineEdit_2.text())
        adres_org = str(self.lineEdit_3.text())
        login = str(self.lineEdit_4.text())
        password = str(self.lineEdit_5.text())
        type = str(self.orgTypes.currentText())
        typeID = self.type_id[type]  # Переводим тип в id для базы данных
        invisible_password = hashlib.sha384(
            (hashlib.sha384((password + 'KARGIN_VLADIMIR').encode()).hexdigest()).encode()).hexdigest()
        que = "INSERT INTO Organization(Name,Address,Login,Password,Type) VALUES(?,?,?,?,?)"
        self.cur.execute(que, (name_org, adres_org, login, invisible_password, typeID))  # Заполняем базу данных
        self.con.commit()
        tranzaction_creater({'Name': name_org, 'Address': adres_org, 'Login': login, 'Password': invisible_password,
                             'Type': typeID})

    def set_orgTypes(self):
        result = self.cur.execute("""SELECT RowId,Name FROM OrganizationType""").fetchall()
        for element in result:
            self.type_id[element[1]] = element[0]  # Заполнения словоря
            self.orgTypes.addItem(element[1])  # Заполнения comboBox


class Arenda(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('аренда.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.type_vag = {}
        self.set_vagon()
        self.pushButton.clicked.connect(self.save_results)

    def save_results(self):
        global organization_now
        number_vagon = str(self.comboBox.currentText())
        stoimost = self.set_stoimost(number_vagon)
        startArenda = self.startArenda.dateTime()
        endArenda = self.endArenda.dateTime()
        startArenda = '.'.join(str(startArenda)[23:-1].split(', ')[2::-1]) + ' ' + \
                      ':'.join(str(startArenda)[23:-1].split(', ')[3:])
        endArenda = '.'.join(str(endArenda)[23:-1].split(', ')[2::-1]) + ' ' + \
                    ':'.join(str(endArenda)[23:-1].split(', ')[3:])
        stoimost = stoimost * (int((endArenda.split())[0].split('.')[2]) -
                               int((startArenda.split())[0].split('.')[2]))
        typeCode = self.type_vag[number_vagon]
        path = tranzaction_creater({'number_vagona': number_vagon, 'type_vagona': typeCode, 'date_start_arenda': startArenda,
                             'date_end_arenda': endArenda, 'stoimost': stoimost, 'arendator': organization_now})
        que = """INSERT INTO Arenda(number_vagona,type_vagona,date_start_arenda,date_end_arenda,stoimost,arendator,path) 
        VALUES(?,?,?,?,?,?,?)"""
        self.cur.execute(que, (number_vagon, typeCode, startArenda, endArenda, stoimost, organization_now,path))
        que2 = f"UPDATE Vagoni SET Arenduuschiy={organization_now} WHERE Number={number_vagon}"
        self.cur.execute(que2)
        self.con.commit()
        arenda.hide()

    def set_stoimost(self, num_vag):
        result = self.cur.execute(f"""SELECT StoimostArendi FROM Vagoni WHERE Number={num_vag}""").fetchall()
        return result[0][0]

    def set_vagon(self):
        result = self.cur.execute("""SELECT Number,Type FROM Vagoni""").fetchall()
        for element in result:
            self.comboBox.addItem(str(element[0]))
            self.type_vag[str(element[0])] = element[1]


class Avtorizasia(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('авторизация.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.pushButton.clicked.connect(self.proverka)

    def proverka(self):
        global organization_now, type_organization_now, arenda, nakladnaya, dobavOrg, dobavVag, perehEkran, OpNaSt, \
            reytSob, reytExp, infoOStansii, poiskVag, karta
        proverka = self.cur.execute("""SELECT Login,Password,ID,Type FROM Organization""").fetchall()
        Login = str(self.lineEdit_4.text())
        Password = str(self.lineEdit_5.text())
        INPassword = hashlib.sha384((hashlib.sha384((Password + 'KARGIN_VLADIMIR').encode()).hexdigest()).encode()).hexdigest()
        for akk in proverka:
            if str(akk[0]) == Login and str(akk[1]) == INPassword:
                organization_now = str(akk[2])
                type_organization_now = akk[3]
                avtoriz.hide()
                perehEkran = PerehEkran()
                perehEkran.show()


class Vagoni(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('вагоны.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.code_type = {}
        self.name_rowId = {}
        self.set_vgTypes()
        self.set_org()
        self.pushButton.clicked.connect(self.save_results)

    def save_results(self):
        numberVagona = str(self.lineEdit_2.text())
        vladelesVagona = str(self.org.currentText())
        type = str(self.vgTypes.currentText())
        stoimost = str(self.lineEdit.text())
        sostVag = str(self.comboBox.currentText())
        Code = self.code_type[type]
        ID = self.name_rowId[vladelesVagona]
        que = "INSERT INTO Vagoni(Number,Type,Vladeles,StoimostArendi,SostVag) VALUES(?,?,?,?,?)"
        self.cur.execute(que, (numberVagona, Code, ID, stoimost, sostVag))
        self.con.commit()
        tranzaction_creater({'Number': numberVagona, 'Type': Code, 'Vladeles': ID, 'StoimostArendi': stoimost,
                             'SostVag': sostVag})

    def set_vgTypes(self):
        result = self.cur.execute("""SELECT Code,Name FROM VagonType""").fetchall()
        for element in result:
            self.code_type[element[1]] = element[0]
            self.vgTypes.addItem(element[1])

    def set_org(self):
        result = self.cur.execute("""SELECT RowId,Name,Type FROM Organization""").fetchall()
        for element in result:
            if element[2] == 4:
                self.name_rowId[element[1]] = element[0]
                self.org.addItem(str(element[1]))


class Nakladnaya(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('накладная.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.set_NumberVagona()
        self.Gruzopoluchatel = {}
        self.set_Gruzopoluchatel()
        self.Gruzoperevozchik = {}
        self.set_Gruzoperevozchik()
        self.Gruz = {}
        self.set_Gruz()
        self.StansiaOtpravlenia = {}
        self.set_StansiaOtpravlenia()
        self.StansiaNaznachenia = {}
        self.set_StansiaNaznachenia()
        self.pushButton.clicked.connect(self.save_results)

    def save_results(self):
        global organization_now
        numberNakladnoy = int(self.lineEdit_4.text())
        vesGruza = int(self.lineEdit_6.text())
        srokDostavki = int(self.lineEdit_2.text())
        stoimostPerevozki = int(self.lineEdit_3.text())
        nVag = int(self.numberV.currentText())
        gruzopo = str(self.gruzopo.currentText())
        gruzope = str(self.gruzope.currentText())
        gruz = str(self.gruz.currentText())
        sOtp = str(self.stOtp.currentText())
        sNaz = str(self.stNaz.currentText())
        dateStart = '.'.join(str(self.dateTimeEdit.dateTime())[23:-1].split(', ')[2::-1]) + ' ' + \
                    ':'.join(str(self.dateTimeEdit.dateTime())[23:-1].split(', ')[3:])
        gruzopo = self.Gruzopoluchatel[gruzopo]
        gruzope = self.Gruzoperevozchik[gruzope]
        gruz = self.Gruz[gruz]
        sOtp = self.StansiaOtpravlenia[sOtp]
        sNaz = self.StansiaNaznachenia[sNaz]
        path = tranzaction_creater(
            {'NumberNakladnoy': numberNakladnoy, 'NumberVagon': nVag, 'Gruzootpravitel': int(organization_now),
             'Gruzopoluchatel': gruzopo, 'Gruzoperevozchik': gruzope, 'Gruz': gruz,
             'VesGruza': vesGruza, 'StartStation': sOtp, 'OverStation': sNaz,
             'DateOtpravleniya': dateStart, 'SrokDostavki': srokDostavki, 'Stoimost': stoimostPerevozki})
        que = """INSERT INTO Nakladnie(NumberNakladnoy,NumberVagon,Gruzootpravitel,Gruzopoluchatel,Gruzoperevozchik,Gruz
        ,VesGruza,StartStation,OverStation,DateOtpravleniya,SrokDostavki,Stoimost,path) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        self.cur.execute(que, (numberNakladnoy, nVag, organization_now, gruzopo, gruzope, gruz, vesGruza, sOtp, sNaz,
                               dateStart, srokDostavki, stoimostPerevozki,path))
        self.con.commit()
        nakladnaya.hide()

    def set_NumberVagona(self):
        result = self.cur.execute("""SELECT Number FROM Vagoni""").fetchall()
        for element in result:
            self.numberV.addItem(str(element[0]))

    def set_Gruzopoluchatel(self):
        result = self.cur.execute("""SELECT RowId,Name,Type FROM Organization""").fetchall()
        for element in result:
            if element[2] == 3:
                self.Gruzopoluchatel[element[1]] = element[0]
                self.gruzopo.addItem(str(element[1]))

    def set_Gruzoperevozchik(self):
        result = self.cur.execute("""SELECT RowId,Name,Type FROM Organization""").fetchall()
        for element in result:
            if element[2] == 1:
                self.Gruzoperevozchik[element[1]] = element[0]
                self.gruzope.addItem(str(element[1]))

    def set_Gruz(self):
        result = self.cur.execute("""SELECT Code,Name FROM GruzType""").fetchall()
        for element in result:
            self.Gruz[element[1]] = element[0]
            self.gruz.addItem(element[1])

    def set_StansiaOtpravlenia(self):
        result = self.cur.execute("""SELECT ID,Name,Type FROM Organization""").fetchall()
        for element in result:
            if element[2] == 5:
                self.StansiaOtpravlenia[element[1]] = element[0]
                self.stOtp.addItem(element[1])

    def set_StansiaNaznachenia(self):
        result = self.cur.execute("""SELECT ID,Name,Type FROM Organization""").fetchall()
        for element in result:
            if element[2] == 5:
                self.StansiaNaznachenia[element[1]] = element[0]
                self.stNaz.addItem(element[1])


class PerehEkran(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('переходное меню.ui', self)
        self.hide_botten()
        self.arenda.clicked.connect(self.ar)
        self.rSob.clicked.connect(self.RS)
        self.nakladnaya.clicked.connect(self.na)
        self.rEks.clicked.connect(self.RE)
        self.avtorizasia.clicked.connect(self.av)
        self.poiskVagonov.clicked.connect(self.PV)
        self.infoOStansii.clicked.connect(self.IOS)
        self.dobVag.clicked.connect(self.DV)
        self.dobOrg.clicked.connect(self .DO)
        self.OperationNaStansii.clicked.connect(self.ONS)
        self.kartaMarshruta.clicked.connect(self.kart)
        self.predlojenia.clicked.connect(self.PR)

    def hide_botten(self):
        global type_organization_now
        if type_organization_now != 6:
            self.dobVag.setHidden(True)
            self.dobOrg.setHidden(True)
        else:
            self.kartaMarshruta.setHidden(True)
            self.infoOStansii.setHidden(True)
            self.poiskVagonov.setHidden(True)
        if type_organization_now != 5:
            self.OperationNaStansii.setHidden(True)
        if type_organization_now != 4:
            self.rEks.setHidden(True)
        if type_organization_now != 1:
            self.arenda.setHidden(True)
            self.rSob.setHidden(True)
        if type_organization_now != 2:
            self.nakladnaya.setHidden(True)
        else:
            self.rEks.setHidden(False)
            self.rSob.setHidden(False)
        if type_organization_now == 4:
            self.rSob.setHidden(False)
        if type_organization_now == 1:
            self.rEks.setHidden(False)

    def RS(self):
        global reytSob
        reytSob = reyting_sobstvennikov()
        reytSob.show()

    def RE(self):
        global reytExp
        reytExp = reyting_Ekspeditorov()
        reytExp.show()

    def IOS(self):
        global infoOStansii
        infoOStansii = InfoAboutStation()
        infoOStansii.show()

    def PV(self):
        global poiskVag
        poiskVag = PoiskVag()
        poiskVag.show()

    def ONS(self):
        global OpNaSt
        OpNaSt = operasii_na_stansii()
        OpNaSt.show()

    def ar(self):
        global arenda
        arenda = Arenda()
        arenda.show()

    def na(self):
        global nakladnaya
        nakladnaya = Nakladnaya()
        nakladnaya.show()

    def av(self):
        global avtoriz
        avtoriz.show()

    def DV(self):
        global dobavVag
        dobavVag = Vagoni()
        dobavVag.show()

    def DO(self):
        global dobavOrg
        dobavOrg = Organizasii()
        dobavOrg.show()

    def kart(self):
        global karta
        karta = Karta()
        karta.show()

    def PR(self):
        global predloj
        predloj = Predlojenia()
        predloj.show()


class operasii_na_stansii(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('операция на станции.ui', self)
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.Name_ID = {}
        self.Number_ID = {}
        self.set_TypeOper()
        self.set_NumberNak()
        self.pushButton.clicked.connect(self.save_results)

    def save_results(self):
        global organization_now
        Nnak = int(self.Nnak.currentText())
        self.Nnakk = Nnak
        self.set_NumberVagona()
        Nvag = self.Nvag
        TypeOp = str(self.TypeOp.currentText())
        Nnak = self.Number_ID[int(Nnak)]
        TypeOp = self.Name_ID[TypeOp]
        dateOperasii = '.'.join(str(self.dateTimeEdit.dateTime())[23:-1].split(', ')[2::-1]) + ' ' + \
                       ':'.join(str(self.dateTimeEdit.dateTime())[23:-1].split(', ')[3:])
        otmetka = self.textEdit.toPlainText()
        que = """INSERT INTO OperationOnStation(Nakladnaya,NumberVag,TypeOperation,DateOperasii,
              OtmetkaObIzmeneniiInfoPoGruzu,Stansia) VALUES(?,?,?,?,?,?)"""
        self.cur.execute(que, (Nnak, Nvag, TypeOp, dateOperasii, otmetka, organization_now))
        self.con.commit()
        tranzaction_creater({'Nakladnaya':Nnak,'NumberVag':Nvag,'TypeOperation':TypeOp,'DateOperasii':dateOperasii,
              'OtmetkaObIzmeneniiInfoPoGruzu':otmetka,'Stansia':int(organization_now)})
        OpNaSt.hide()

    def set_TypeOper(self):
        result = self.cur.execute("""SELECT ID,Name FROM TypeOperation""").fetchall()
        for element in result:
            self.Name_ID[element[1]] = element[0]
            self.TypeOp.addItem(element[1])

    def set_NumberVagona(self):
        result = self.cur.execute("""SELECT NumberVagon,NumberNakladnoy FROM Nakladnie""").fetchall()
        for element in result:
            if self.Nnakk == element[1]:
                self.Nvag = int(element[0])

    def set_NumberNak(self):
        result = self.cur.execute("""SELECT ID,NumberNakladnoy FROM Nakladnie""").fetchall()
        for element in result:
            self.Number_ID[element[1]] = element[0]
            self.Nnak.addItem(str(element[1]))


class reyting_Ekspeditorov(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Рейтинг экспедиторов.ui', self)
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.name_rowId = {}
        self.set_eks()
        self.pushButton_2.clicked.connect(self.save_results)

    def save_results(self):
        ekspeditor = str(self.comboBox.currentText())
        ekspeditor = str(self.name_rowId[ekspeditor])
        otzif = self.textEdit.toPlainText()
        que = "UPDATE Organization SET Otzivi = '" + otzif + "' WHERE ID = " + ekspeditor
        self.cur.execute(que)
        self.con.commit()
        reytExp.hide()

    def otp_zapros(self):
        pass

    def set_eks(self):
        result = self.cur.execute("""SELECT  o.ID,o.Name,o.Type,o.Otzivi,count(n.ID) kol,
        sum(n.VesGruza)/count(n.ID) srVes,sum(n.Stoimost)/count(n.ID) srStoimost FROM Organization o 
        LEFT JOIN Nakladnie n ON o.ID=n.Gruzoperevozchik GROUP BY o.ID,o.Name,o.Type,o.Otzivi;""").fetchall()
        rowPosition = 0
        for element in result:
            if element[2] == 1:
                rowPosition += 1
                if rowPosition != 1:
                    self.tableWidget.insertRow(rowPosition)
                self.name_rowId[element[1]] = element[0]
                self.comboBox.addItem(str(element[1]))
                self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(str(element[1])))
                self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(str(element[4])))
                self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(element[5])))
                self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(element[6])))
                self.tableWidget.setItem(rowPosition, 4, QTableWidgetItem(str(element[3])))


class reyting_sobstvennikov(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('рейтинг собственников.ui', self)
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.ID_Name = {}
        self.Name_ID = {}
        self.set_table()
        self.pushButton_2.clicked.connect(self.save_results)

    def save_results(self):
        sobstvennik = str(self.comboBox.currentText())
        sobstvennik = str(self.Name_ID[sobstvennik])
        otzif = self.textEdit.toPlainText()
        que = "UPDATE Organization SET Otzivi = '" + otzif + "' WHERE ID = " + sobstvennik
        self.cur.execute(que)
        self.con.commit()
        reytSob.hide()

    def otp_zapros(self):
        pass

    def set_table(self):
        result = self.cur.execute("""SELECT  v.Vladeles,sum(v.StoimostArendi)/count(v.Number),count(v.Number),va.SostVag
         From Vagoni v Left Join (SELECT v1.Vladeles,v1.SostVag,COUNT(*) cnt FROM Vagoni v1  GROUP 
         BY v1.Vladeles,v1.SostVag) va on v.Vladeles=va.Vladeles GROUP By 
         v.Vladeles,va.SostVag,va.cnt ORDER BY v.Vladeles,va.cnt DESC;""").fetchall()
        result1 = self.cur.execute("""SELECT Vladeles,Number FROM Vagoni""").fetchall()
        result2 = self.cur.execute("""SELECT ID,Name,Type FROM Organization""").fetchall()
        result_ = []
        for i in result:
            Tr = True
            for i1 in result_:
                if i[0] == i1[0]:
                    Tr = False
            if Tr:
                result_.append(i)
        result = result_
        for element in result2:
            if element[2] == 4:
                self.Name_ID[element[1]] = element[0]
                self.ID_Name[element[0]] = element[1]
        for element in result2:
            if element[2] == 4:
                self.comboBox.addItem(str(element[1]))
        rowPosition = 0
        for element in result:
            Vagoni = []
            rowPosition += 1
            for i in result1:
                if i[0] == element[0]:
                    Vagoni.append(str(i[1]))
            if rowPosition != 1:
                self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(self.ID_Name[element[0]]))
            self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(str(element[1])))
            self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(element[3])))
            self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(element[2])))
            self.tableWidget.setItem(rowPosition, 4, QTableWidgetItem(', '.join(Vagoni)))


class PoiskVag(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('поиск вагонов.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.set_table()

    def set_table(self):
        result = self.cur.execute("""with a as(
        SELECT v.Number,t.name typeName,vl.name vladName,v.SostVag,an.name arName,g.Name gruzName,v1.VesGruza,tip.Name 
        TypeOpName,v2.DateOperasii,st.Name stName,ar.date_start_arenda,ar.date_end_arenda,row_number() over (partition 
        by v.Number order by v2.DateOperasii desc) rn
        FROM Vagoni v 
        LEFT JOIN VagonType t on t.code=v.type
        LEFT JOIN Organization vl on vl.id=v.vladeles
        LEFT JOIN Organization an on an.id=v.Arenduuschiy
        LEFT JOIN OperationOnStation v2 on v2.NumberVag=v.Number 
        LEFT JOIN Organization st on st.id=v2.Stansia
        LEFT JOIN TypeOperation tip on tip.id=v2.TypeOperation
        LEFT JOIN Nakladnie v1 on v.Number=v1.NumberVagon and v1.ID=IFNULL(v2.Nakladnaya,v1.ID) 
        LEFT JOIN GruzType g on g.code=v1.Gruz
        LEFT JOIN Arenda ar on ar.number_vagona=v.Number)
        select * from a where rn=1;""").fetchall()
        rowPosition = 0
        for element in result:
            rowPosition += 1
            if rowPosition != 1:
                self.tableWidget.insertRow(rowPosition)
            self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(str(element[0])))
            self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(str(element[1])))
            self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(element[2])))
            self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(element[3])))
            self.tableWidget.setItem(rowPosition, 4, QTableWidgetItem(str(element[4])))
            self.tableWidget.setItem(rowPosition, 5, QTableWidgetItem(str(element[10])))
            self.tableWidget.setItem(rowPosition, 6, QTableWidgetItem(str(element[11])))
            self.tableWidget.setItem(rowPosition, 7, QTableWidgetItem(str(element[9])))
            self.tableWidget.setItem(rowPosition, 8, QTableWidgetItem(str(element[8])))
            self.tableWidget.setItem(rowPosition, 9, QTableWidgetItem(str(element[7])))
            self.tableWidget.setItem(rowPosition, 10, QTableWidgetItem(str(element[5])))
            self.tableWidget.setItem(rowPosition, 11, QTableWidgetItem(str(element[6])))


class InfoAboutStation(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('Инфо о станции.ui', self)  # Загружаем дизайн
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.Name_ID = {}
        self.set_table()
        self.pushButton_2.clicked.connect(self.save_results)

    def save_results(self):
        station = str(self.comboBox_2.currentText())
        station = str(self.Name_ID[station])
        otzif = self.textEdit.toPlainText()
        que = "UPDATE Organization SET Otzivi = '" + otzif + "' WHERE ID = " + station
        self.cur.execute(que)
        self.con.commit()

    def set_table(self):
        result = self.cur.execute("""SELECT o.ID,o.Name,o.Otzivi,count(os.NumberVag),count(DISTINCT os.NumberVag) FROM 
        Organization o LEFT JOIN OperationOnStation os on os.Stansia=o.ID WHERE o.type=5 group by o.ID,o.Name,o.Otzivi
        ;""").fetchall()
        rowPosition = 0
        for element in result:
            rowPosition += 1
            if rowPosition != 1:
                self.tableWidget.insertRow(rowPosition)
            self.Name_ID[element[1]] = element[0]
            self.comboBox_2.addItem(element[1])
            self.tableWidget.setItem(rowPosition, 0, QTableWidgetItem(str(element[1])))
            self.tableWidget.setItem(rowPosition, 1, QTableWidgetItem(str(element[4])))
            self.tableWidget.setItem(rowPosition, 2, QTableWidgetItem(str(element[3])))
            self.tableWidget.setItem(rowPosition, 3, QTableWidgetItem(str(element[2])))


class Karta(QWidget):
    def __init__(self):
        super().__init__()
        self.con = sqlite3.connect("ASUgruzoperevozki.db")
        self.cur = self.con.cursor()
        self.koord = [[151, 210, 7], [455, 405, 8], [759, 264, 9], [1012, 439, 10], [656, 635, 11], [1446, 605, 14],
                      [1612, 216, 15]]
        self.biger_koord = []
        self.initUI()

    def initUI(self):
        for elem in self.koord:
            for razbros_x in range(-30, 30):
                for razbros_y in range(-30, 30):
                    self.biger_koord.append([elem[0] + razbros_x, elem[1] + razbros_y, elem[2]])
        self.setGeometry(50, 50, 1840, 720)
        self.setWindowTitle('Вторая программа')
        label = QLabel(self)
        pixmap = QPixmap('карта.png')
        label.setPixmap(pixmap)

        self.label1 = QLabel(self)
        self.label1.resize(200, 30)
        self.label1.setText("None")
        self.label1.move(2000, 800)

        self.label2 = QLabel(self)
        self.label2.resize(200, 30)
        self.label2.setText("None")
        self.label2.move(2000, 800)

    def mouseMoveEvent(self, event):
        for elem in self.biger_koord:
            if elem[0] == event.x() and elem[1] == event.y():
                self.get_adres_name(elem[2], event.x(), event.y())

    def get_adres_name(self, id, x, y):
        result = self.cur.execute(f"""SELECT Name,Address FROM Organization WHERE ID={id};""").fetchall()
        self.label1.move(x, y)
        self.label2.move(x, y + 15)
        self.label1.setText(result[0][0])
        self.label2.setText(result[0][1])


directory_of_T = 'Tranzactions/'
files_ = os.listdir(directory_of_T)
type_organization_now = 0
organization_now = 0
pubK = json.load(open('Открытый ключ.txt'))
pubK = rsa.PublicKey(e=pubK['e'], n=pubK['n'])
prK = json.load(open('Закрытый ключ.txt'))
prK = rsa.PrivateKey(e=prK['e'], n=prK['n'], d=prK['d'], p=prK['p'], q=prK['q'])
# block_creater([json.dumps(json.load(open(directory_of_T + str(i) + '.json')), separators=(',', ':')) for i in range(len(files_))])
arenda = None
nakladnaya = None
dobavVag = None
dobavOrg = None
perehEkran = None
OpNaSt = None
reytSob = None
reytExp = None
infoOStansii = None
poiskVag = None
karta = None
predloj = None
if __name__ == '__main__':
    app = QApplication(sys.argv)
    avtoriz = Avtorizasia()
    avtoriz.show()
    sys.exit(app.exec_())
