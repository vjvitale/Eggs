import SocketServer
import codecs
import json
from enum import Enum
import ssl
from re import search
import random
import bcrypt
import csv
import string

#used for naming images
image_counter = 0
msg = []


#used for passwords

usertable = {}

tokentable ={}

with open("eggtokens.txt") as filey2:
	csvread = csv.reader(filey2)
	for line in csvread:
		if line[0] in tokentable.keys():
			tokentable[line[0]].append(line[1])
		else:
			tokentable[line[0]] = [line[1]]
	filey2.close()

with open("eggwords.txt", "r") as filey:
	csvread = csv.reader(filey)
	for line in csvread:
		usertable[line[0]] = line[1]
	filey.close()

class R_TYPE(Enum):
	html = 1
	css = 2
	png = 3
	txt = 4
	js = 5
	redirect = 6
	fail = 7
	txt_file = 8
	html_form = 9

class HTTPHandler(SocketServer.BaseRequestHandler):
	lnBreak = "\r\n"
	response_header ={ "Content-Type" : "", "Content-Length": "", "X-Content-Type-Options" : "nosniff"}
	recieve_header = {}

	#response type info
	response_type = ""
	gp_req = ""

	def genRandomToken(self):
		options = string.ascii_lowercase + string.ascii_uppercase + string.digits
		retVal = ""
		for i in range(16):
			retVal += random.choice(options)

		return retVal


	def createDict(self, posty):
		msg = posty.split("&")
		retVal = {}
		for mess in msg:
			keyval = mess.split("=")
			if len(keyval) >= 2:
				retVal[keyval[0]] = keyval[1]
			else:
				retVal[keyval[0]] = ""
		return retVal


	def createReadFile(self, filename):
		body = ""
		with codecs.open(filename, 'r', "utf-8") as f:
			for line in f:
				body += line
		self.response_header["Content-Length"] = str(len(body.encode('utf-8')))

		return body

	def write_image(self,lines, filename):
		with open(filename, 'wb') as fw:
			fw.write(lines)

	def createImageFile(self, filename):
		body = ""
		with open(filename, "rb") as f:
			body = f.read()
		self.response_header["Content-Length"] = str(len(body))

		return body

	def createPlainText(self, text):
		body = text
		self.response_header["Content-Length"] = str(len(body.encode('utf-8')))	
		return body

	def createHTMLForm(self, form):
		body = ""
		with codecs.open(form, 'r') as f:
			line = f.readline()
			while line != None:
				if "{{loop_start}}" in line:
					line = f.readline()
					while "{{loop_end}}" not in line:
						with open("eggImages.txt") as eggies:
							for eggs in eggies:
								body += line.replace("{{source}}", eggs.strip("\r\n"))
						line = f.readline()
					line = f.readline()
				else:			
					body += line
				line = f.readline()

		self.response_header["Content-Length"] = str(len(body.encode('utf-8')))

		return body

	def determineContentType(self, rType):
		if rType == R_TYPE.html or rType == R_TYPE.html_form:
			self.response_header["Content-Type"] = "text/html; charset=utf-8"
		elif rType == R_TYPE.css:
			self.response_header["Content-Type"] = "text/css; charset=utf-8"
		elif rType == R_TYPE.png:
			self.response_header["Content-Type"] = "image/png; charset=ascii"
		elif rType == R_TYPE.js:
			self.response_header["Content-Type"] = "text/javascript; charset=utf-8"
		else:
			self.response_header["Content-Type"] = "text/plain; charset=utf-8"	

	def organizeHeaders(self):
		retVal = ""

		for header in self.response_header.keys():
			retVal += header + ":" + self.response_header[header] + self.lnBreak

		return retVal		

	def createGetResponse(self, rType, bodyInfo):
		response_boi = ""
		body = ""
		if rType == R_TYPE.redirect:
			response_boi = "HTTP/1.1 301 SWITCH"
			self.response_header["Location"] = bodyInfo
			self.response_header["Content-Length"] = "0"
		
		elif rType == R_TYPE.fail:
			response_boi = "HTTP/1.1 404 ERROR"
			body = self.createPlainText("Page not found UwU")

		elif rType == R_TYPE.txt:
			response_boi = "HTTP/1.1 200 OK"
			body = self.createPlainText(bodyInfo)

		elif rType == R_TYPE.png:
			response_boi = "HTTP/1.1 200 OK"
			body = self.createImageFile(bodyInfo)

		elif rType == R_TYPE.html_form:
			response_boi = "HTTP/1.1 200 OK"
			body = self.createHTMLForm(bodyInfo)

		else:
			response_boi = "HTTP/1.1 200 OK"
			body = self.createReadFile(bodyInfo)
		self.determineContentType(rType)
		response_boi += self.lnBreak + self.organizeHeaders() + self.lnBreak + body

		return response_boi

	def write_file(self, lines, filename):
		with open(filename, 'a') as fw:
			fw.writelines(lines)

	def determineRecievedHeaders(self, lines):


		for line in lines:
			if ":" not in line:
				continue

			line = line.split(":")
			self.recieve_header[line[0]] = line[1]


	def eggQuery(self, q_string):
		query = q_string.split("&")
		name = ""
		num = ""
		for q in query:
					qy = q.split("=")
					if qy[0] == "name":
						name = qy[1]
					if qy[0] == "num":
						num = qy[1]

		return "Hello " + name + " you ate " + num + " eggs today."

	def storeMessage(self, msg_response):
		global msg

		if len(msg) > 20:
			msg = msg[1:]
			msg.append(msg_response)
		else:
			msg.append(msg_response)



	def handle(self):

		global usertable
		global tokentable
		self.recieve_header = {}
		self.response_header ={ "Content-Type" : "", "Content-Length": "", "X-Content-Type-Options" : "nosniff"}

		self.data = self.request.recv(1024)

		

		lines = self.data.split('\r\n')
		
		if len(lines) < 2:
			return

		egg = lines[0].split(" ")

		self.response_type = egg[1]
		self.gp_req = egg[0]

		self.determineRecievedHeaders(lines)

		post = ""

		if self.gp_req == "POST":

			post = self.data.split(self.lnBreak + self.lnBreak)[1]



		response_boi = ""

		if self.gp_req == "GET":

			if self.response_type == "/":
				if "Cookie" not in self.recieve_header.keys():
					self.response_header["Set-Cookie"] = "visited=1"
					response_boi = self.createGetResponse(R_TYPE.html, "EggsFirst.html")
				else:
					response_boi = self.createGetResponse(R_TYPE.html, "EggsIntro.html")
			elif self.response_type == "/style.css":
				response_boi = self.createGetResponse(R_TYPE.css, "style.css")
			elif self.response_type == "/welcome":
				response_boi = self.createGetResponse(R_TYPE.txt, "I like eggs")
			elif self.response_type == "/switch":
				response_boi = self.createGetResponse(R_TYPE.redirect, "/welcome")
			elif self.response_type == "/EggsRecipes":
				if "Cookie" not in self.recieve_header.keys():
					self.response_header["Set-Cookie"] = "visited=1"
					response_boi = self.createGetResponse(R_TYPE.html, "EggRecUno.html")
				else:
					response_boi = self.createGetResponse(R_TYPE.html, "EggsRecipes.html")
			elif self.response_type == "/buttons.js":
				response_boi = self.createGetResponse(R_TYPE.js, "buttons.js")
			elif self.response_type == "/eggie.png":
				response_boi = self.createGetResponse(R_TYPE.png, "eggie.png")
			elif self.response_type.startswith("/query"):
				response_boi = self.createGetResponse(R_TYPE.txt, self.eggQuery(self.response_type.split("?")[1]))
			elif self.response_type == "/egg_form":
				response_boi = self.createGetResponse(R_TYPE.html, "egg_form.html")
			elif self.response_type == "/image":
				response_boi = self.createGetResponse(R_TYPE.html, "egg_images.html")
			elif self.response_type.startswith("/images"):
				response_boi = self.createGetResponse(R_TYPE.png, self.response_type.split("s/")[1])
			elif self.response_type == "/allImages":
				response_boi = self.createGetResponse(R_TYPE.html_form, "html_form.html")
			elif self.response_type == "/chat":
				response_boi = self.createGetResponse(R_TYPE.html, "chatting.html")
			elif self.response_type == "/WelcomeChat":
				response_boi = self.createGetResponse(R_TYPE.txt, "<p>Welcome Please keep the topic relevant to eggs!</p>")
			elif self.response_type =="/dispMessage":
				global msg

				retVal = "<p>"

				for mess in msg:
					retVal += mess + "<br>"
				retVal +="</p>" 

				response_boi = self.createGetResponse(R_TYPE.txt, retVal)
			elif self.response_type == "/eggsecrets":
				response_boi = self.createGetResponse(R_TYPE.html, "eggsecrets.html")
			elif self.response_type =="/eggsecrets2":
				response_boi = self.createGetResponse(R_TYPE.html, "eggsecrets2.html")
			elif self.response_type == "/eggssecretsunleashed":
				if "Cookie" not in self.recieve_header.keys():
					response_boi = self.createGetResponse(R_TYPE.redirect, "/eggsecrets2")
				else:
					cookies = self.recieve_header["Cookie"].split('; ')
					cookiedict = {}
					for cookie in cookies:
						c = cookie.strip().split("=")
						cookiedict[c[0]] = c[1]
					if "token" not in cookiedict.keys():
						response_boi = self.createGetResponse(R_TYPE.redirect, "/eggsecrets2")
					else:
						token = cookiedict["token"]
						found = False
						for key in tokentable.keys():
							for val in tokentable[key]:
								if bcrypt.checkpw(token, val):
									found = True
									resp = "hello " + key + ", did you know you know there are approximately 23.7 Billion chickens in the world!"
									response_boi = self.createGetResponse(R_TYPE.txt,  resp)
									break
							if found:
								break
						if not found:
							response_boi = self.createGetResponse(R_TYPE.redirect, "/eggsecrets2")
			else:
				response_boi = self.createGetResponse(R_TYPE.fail, "")

		else:
			if self.response_type == "/vitcors":
				values = post.split("&")
				sentance = values[0].split("=")[1] + " ate " + values[1].split("=")[1] + " eggs.\n"
				self.write_file([sentance], "eggs.txt")

				response_boi = self.createGetResponse(R_TYPE.txt_file, "eggs.txt")

			elif self.response_type == "/image":
				global image_counter
				#post = post.split("Content-Type: image/png")[1]

				imgName = "image"+str(image_counter)+".png"
				
				self.write_file(["images/"+ imgName, self.lnBreak], "eggImages.txt")
				self.write_image(post, imgName) 
				response_boi = self.createGetResponse(R_TYPE.redirect, "/images/" + imgName)
				image_counter += 1

			elif self.response_type == "/sendMessage":
				posty = json.loads(post)
				self.storeMessage(posty)
			elif self.response_type == "/register":
				eggsD = self.createDict(post)

				failed = False

				faileddict = {"usercompliance" : "none", "passLen" : "none", "passcaps" : "none", "passnum" : "none", "succesreg" : "none"}
				print(usertable)
				if eggsD["name"] in usertable.keys():
					failed = True
					faileddict["usercompliance"] = "block"

				passw = eggsD["pass"]
				if len(passw) < 15:
					failed = True
					faileddict["passLen"] = "block"
				if not search("[A-Z]", passw):
					failed = True
					faileddict["passcaps"] = "block"
				if not search(".*[0-9].*[0-9].*", passw):
					failed = True
					faileddict["passnum"] = "block"

				if failed:
					response_boi = self.createGetResponse(R_TYPE.txt, json.dumps(faileddict))
				else:
					salt = bcrypt.gensalt()
					hashed = bcrypt.hashpw(passw, salt)

					usertable[eggsD["name"]] = hashed

					with open("eggwords.txt", 'a+') as eggwords:
						csvwriter = csv.writer(eggwords)
						csvwriter.writerow([eggsD["name"], hashed])
						eggwords.close()

					faileddict["succesreg"] = "block"

					response_boi = self.createGetResponse(R_TYPE.txt, json.dumps(faileddict))

			elif self.response_type =="/login":
				
				eggsD = self.createDict(post)

				resp = {"loginfailed" : "none"}
				print(usertable)
				if eggsD["name"] in usertable.keys() and bcrypt.checkpw(eggsD["pass"], usertable[eggsD["name"]]):


						token = self.genRandomToken()

						self.response_header["Set-Cookie"] = "token=" + token
						salt = bcrypt.gensalt()
						hashed = bcrypt.hashpw(token, salt)

						if eggsD["name"] in tokentable.keys():
							
							tokentable[eggsD["name"]].append(hashed)
						else:
							salt = bcrypt.gensalt()
							tokentable[eggsD["name"]] = [hashed]


						response_boi = self.createGetResponse(R_TYPE.redirect, "/eggssecretsunleashed")

						with open("eggtokens.txt", 'a+') as eggwords:
							csvwriter = csv.writer(eggwords)
							csvwriter.writerow([eggsD["name"], hashed])
							eggwords.close()

				else:
					response_boi = self.createGetResponse(R_TYPE.redirect, "/eggsecrets2")




		print(self.data)
		print(response_boi)
		self.request.sendall(response_boi)
		

if __name__ == "__main__":
	print("Hello world")
	ssever = SocketServer.TCPServer(('localhost', 8080), HTTPHandler)

	ssever.socket = ssl.wrap_socket(ssever.socket, keyfile="private.key", certfile="cert.pem", server_side=True)

	ssever.serve_forever()
		