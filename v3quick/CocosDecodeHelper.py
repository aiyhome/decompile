#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import getopt
import shutil
import re
import platform
import errno
import zipfile
import subprocess
import CocosXXTEA
#拷文件
#shutil.copy(filename1, filename2)
#拷目录
# shutil.copytree(dirname1, dirname2)

# load xxtea
sysstr = platform.system()
if(sysstr =="Windows"):
    from win32 import xxtea
elif(sysstr == "Linux"):
    print "Liunux Support is coming sooooon"
    sys.exit(-1)
elif(sysstr == "Darwin"):
    from mac import xxtea
else:
    print "Unsupport OS!"
    sys.exit(-1)


#   修改工作目录
def changeWordDir(dir_path):
    ret = -1
    try:
        os.chdir(dir_path)
        ret = 0
    except Exception as e:
    	# 修改目录失败
        ret = -1
    return ret

#   获取脚本文件的当前路径
def curFileDir():
    #获取脚本路径
    path = sys.path[0]
    #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.dirname(path)

# 压缩zip文件夹
def zipdir(zipfilepath, outputdir):
	z = zipfile.ZipFile(zipfilepath,'w',zipfile.ZIP_DEFLATED)
	for dirpath, dirnames, filenames in os.walk(outputdir):
		for filename in filenames:
			z.write(os.path.join(dirpath,filename))
	z.close()

# 解压zip文件
def unzip(zipfilepath, outputdir):
	z = zipfile.ZipFile(zipfilepath,'r')
	for filename in z.namelist():
		data = z.read(filename)
		file = open(outputdir + "/" + filename, 'w+b')
		file.write(data)
		file.close()


def checkFileExt(path):
    binExt = [".zip", ".jpg", ".jpeg", ".png", ".pvr", ".ccz", ".bmp", ".csb", ".manifest", ".json"]
    ext = os.path.splitext(path)[1]
    ext = ext.lower()
    return ext in binExt

# 获取所有文件
def getAllFiles(path, prefix, files):
	print(path)
	fl = os.listdir(path) # get what we have in the dir.
	for f in fl:
	    if os.path.isdir(os.path.join(path,f)): # if is a dir.
	        if prefix == '':
	            getAllFiles(os.path.join(path,f), f, files)
	        else:
	            getAllFiles(os.path.join(path,f), prefix + '/' + f, files)
	    else:
	        filename = ''
	        if prefix != '':
	            filename = prefix + '/' + f
	        else:
	            filename = f
	        files.append(filename)
	return files

# 创建多级目录
def mkdir_p(path):
	try:
	    os.makedirs(path)
	except OSError as exc: # Python >2.5 (except OSError, exc: for Python <2.5)
	    if exc.errno == errno.EEXIST and os.path.isdir(path):
	        pass
	    else: raise

# 复制多级目录
def copydir_p(srcPath, dstPath):
	mkdir_p(dstPath)
	for dirpath,dirnames,filenames in os.walk(srcPath):
		path = dirpath.replace(srcPath, dstPath)
		if not os.path.exists(path):
			os.mkdir(path)

def encodeResWithXXTEA(rootdir, filepath, key, sign, outputdir):
    buff = ""
    src = rootdir + "/" + filepath
    inFp = open(src, 'rb')
    for line in inFp.readlines(): 
        buff += line
    inFp.close()

    if not checkFileExt(src):
        # xxtea encoder
		if data == '':
			buff = sign + data
		else:
			buff = sign + xxtea.encrypt(buff, key)


    dest = outputdir + "/" + filepath
    outFp = open(dest, 'wb')
    outFp.write(buff)
    outFp.close()

def decodeResWithXXTEA(rootdir, filepath, key, sign, outputdir):
	buff = ""
	print rootdir, filepath
	src = rootdir + "/" + filepath
	inFp = open(src, 'rb')
	for line in inFp.readlines(): 
		buff += line
	inFp.close()
	if not checkFileExt(src):
		if buff[:len(sign)] == sign:
			data = buff[len(sign):]
			if data == '':
				buff = data
			else:
				buff = xxtea.decrypt(data, key)
	dest = outputdir + "/" + filepath
	outFp = open(dest, 'wb')
	outFp.write(buff)
	outFp.close()

def encodeDir(dirpath, key, sign, outputdir):
	fileList = []
	fileList = getAllFiles(dirpath, '', fileList)
	copydir_p(dirpath, outputdir)
	for filename in fileList:
		encodeResWithXXTEA(dirpath, filename, key, sign, outputdir)

def decodeDir(dirpath, key, sign, outputdir):
	fileList = []
	fileList = getAllFiles(dirpath, '', fileList)
	copydir_p(dirpath, outputdir)
	for filename in fileList:
		decodeResWithXXTEA(dirpath, filename, key, sign, outputdir)

# 修正key值为16bit
def fixKeyLength(key):
    if len(key) < 16:
        key = key + "\0"*(16 - len(key))
    return key

# java -jar unluac.jar myfile.luac > myfileDecompiled.lua
# myfile.luac 编译后的字节码文件
# myfileDecompiled.lua 字节码反编译的输出文件
def unluac(src, dst):
	unluaccmd = '%s "%s" > "%s"' %(UNLUAC, src, dst)
	# do shell cmd
	print(unluaccmd)
	cmd = subprocess.Popen(unluaccmd, shell = True, stdout = subprocess.PIPE, env = None)
	cmd.wait()

def decompileLuac(targetDir, outputdir):
	mkdir_p(outputdir)
	fileList = []
	fileList = getAllFiles(targetDir, '', fileList)
	for filename in fileList:
		segments = filename.split(".")
		shortname = segments.pop()
		dirpath = "/".join(segments)
		if dirpath != '':
			mkdir_p(outputdir + "/" + dirpath)
		newfilename = dirpath + "/" +shortname +".lua"
		unluac(targetDir + "/" + filename,outputdir + "/"  + newfilename)

def handleLuaChsAscii(match):
	content = match.group(0)
	strSize = len(content)
	if strSize > 2:
		codeArray = content.split("\\")
		count = len(codeArray)
		retStr = ''
		if count > 2:
			for i in range(1, count):
				retStr = retStr + chr(int(codeArray[i]))
		return retStr
	return content

# 修复lua中文ascii显示
def fixLuaChsAscii(filepath):
	buff = ""
	inFp = open(filepath, 'rb')
	for line in inFp.readlines():
		data = re.sub(r'(\\\d\d\d)+', handleLuaChsAscii, line)
		buff += data
	inFp.close()
	outFp = open(filepath, 'wb')
	outFp.write(buff)
	outFp.close()

# 修复所有lua文件中中文乱码
def fixAllLuaChsErrorCode(dirpath):
	fileList = []
	fileList = getAllFiles(dirpath, '', fileList)
	for filename in fileList:
		if filename[-4:] == '.lua':
			print (dirpath + "/" + filename)
			fixLuaChsAscii(dirpath + "/" + filename)


# 解压apk
# java -jar apktool.jar d yourApkFile.apk
#  注意`apktool.jar`是刚才下载后的jar的名称，`d`参数表示decode
#  在这个命令后面还可以添加像`-o -s`之类的参数，例如
#  java -jar apktool.jar d -f yourApkFile.apk -o destiantionDir -s
#  几个主要的参数设置方法及其含义：
# -f 如果目标文件夹已存在，强制删除现有文件夹
# -o 指定反编译的目标文件夹的名称（默认会将文件输出到以Apk文件名命名的文件夹中）
# -s 保留classes.dex文件（默认会将dex文件解码成smali文件）
# -r 保留resources.arsc文件（默认会将resources.arsc解码成具体的资源文件）
def unpackApk(apkfile, outputdir):
	mkdir_p(outputdir)
	unpackcmd = "%s d -f %s -o %s -s" % (APKTOOL, apkfile, outputdir)
	print unpackcmd
	cmd = subprocess.Popen(unpackcmd, shell = True, stdout = subprocess.PIPE, env = None)
	cmd.wait()

# 打包apk
def packApk(srcdir, outapkfile):
	packcmd = "%s b -f %s -o %s" % (APKTOOL, srcdir, outapkfile)
	print packcmd
	cmd = subprocess.Popen(packcmd, shell = True, stdout = subprocess.PIPE, env = None)
	cmd.wait()

# keystore：用于指定 keystore 的位置
# storepass：用于指定 keystore 的密码
# apkfile：表示要签名的文件
# alias：表示 keystore 文件的别名
# jarsigner：安装JDK后在其安装目录bin文件夹下
def signApk(apkfile, keystore, storepass, alias):
	signcmd = "%s -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore %s -storepass %s %s %s" % (JAR_SIGNER,keystore, storepass, apkfile, alias)
	cmd = subprocess.Popen(signcmd, shell = True, stdout = subprocess.PIPE, env = None)
	cmd.wait()

#将dex文件转成jar文件
def convertDexToJar(dexfile, outputfile):
	cvtcmd = "%s %s -o %s" % (DEX2JAR, dexfile, outputfile)
	cmd = subprocess.Popen(cvtcmd, shell = True, stdout = subprocess.PIPE, env = None)
	cmd.wait()

# 从apk中提取一类型的文件
def extractFilesFromApk(filename, outputdir = "", suffix = ""):
	z = zipfile.ZipFile(filename, 'r')
	for f in z.namelist():
		dirpath,name = os.path.split(f)
		ext = os.path.splitext(f)[1]
		if ext == suffix:
			outputdir = outputdir + "/" + dirpath
			mkdir_p(outputdir)
			data = z.read(f)					
			outFp = open(outputdir + "/" + f , 'wb')
			outFp.write(data)
			outFp.close()

# 用jd-gui打开jar文件阅读java代码
def openJarWithJDGUI(jarfilename):
	print jarfilename
	status = subprocess.call(JD_GUI + " " + jarfilename, shell=True)

# 使用jeb反编译class.dex
def decompileWithJEB(classespath):
	jebcmd =  "java -Xmx1430m -jar %s --automation --script=%s %s" % (JEB_JAR, JEBDECOMPILEALL_PY_PATH, classespath)
	print jebcmd
	status = subprocess.call(jebcmd, shell=True)

# 反编译apk
def decompileApk():
	apkname = "com.qqgame.happymj_6.9.73_69730"
	apkdirpath = WORK_DIR + "/bin/" + apkname
	apkfilepath = WORK_DIR + "/bin/" + apkname + ".apk"
	apkdexoutdir = WORK_DIR + "/bin/classes/" + apkname
	if not os.path.exists(apkdirpath):
		unpackApk(apkfilepath, apkdirpath)
	if not os.path.exists(apkdexoutdir + "/classes.dex"):
		mkdir_p(apkdexoutdir)
		shutil.copy(apkdirpath + "/classes.dex", apkdexoutdir + "/classes.dex")
		# extractFilesFromApk(apkfilepath, apkdexoutdir, ".dex")
	decompileWithJEB(apkdexoutdir + "/classes.dex")
	# convertDexToJar(apkdexoutdir + "/classes.dex", apkdexoutdir + "/classes.jar")
	# openJarWithJDGUI(apkdexoutdir + "/classes.jar")

# 反编译quick打包的代码zip包
def decompileLuaCodeZip():
	apkname = "texas_hall"
	key = "{YIIHUA@*@*2017}"
	sign = "YIIHUA@2017"
	apkname = "com.xq5.ncmj_6.4_64"
	key = "XXTEA"
	sign = "XXTEA"
	key = fixKeyLength(key)

	apkdirpath = WORK_DIR + "/bin/" + apkname
	apkfilepath = WORK_DIR + "/bin/" + apkname + ".apk"
	if not os.path.exists(apkdirpath):
		unpackApk(apkfilepath, apkdirpath)
	gamezipdir = WORK_DIR + "/bin/" + apkname + "/assets/res"
	codefilearray = ["game.zip", "framework.zip"]
	outputdir = WORK_DIR + "/bin/codes/" + apkname
	for codefilename in codefilearray:
		if not os.path.exists(outputdir + "/" + codefilename):
			mkdir_p(outputdir)
			decodeResWithXXTEA(gamezipdir, codefilename, key, sign, outputdir)
		codedir = outputdir + "/" + os.path.splitext(codefilename)[0]	
		if not os.path.exists(codedir):
			mkdir_p(codedir)
			unzip(outputdir + "/" + codefilename, codedir)
		# try:
		# 	shutil.rmtree(codedir + "src")
		# except Exception as e:
		# 	pass
		if not os.path.exists(codedir + "src"):
			decompileLuac(codedir, codedir + "src")
		print codedir + "src"
		fixAllLuaChsErrorCode(codedir + "src")


# "java -jar disunity.jar"
# 一花
# key = "{YIIHUA@*@*2017}"
# sign = "YIIHUA@2017"
# 乐抖
# key = "cardKey20170411"
# sign = "cardSign20170411"
if __name__ == "__main__":
	changeWordDir(curFileDir())
	global WORK_DIR
	global UNLUAC
	global APKTOOL
	global JAR_SIGNER
	global DEX2JAR
	global JD_GUI
	WORK_DIR = os.getcwd()
	UNLUAC = WORK_DIR + "/unluac/unluac.bat"
	APKTOOL = WORK_DIR + "/apktool/apktool.bat"
	JAR_SIGNER = os.environ["JAVA_HOME"] + "/bin/jarsigner.exe"
	DEX2JAR = WORK_DIR + "/dex2jar/dex2jar-2.0/d2j-dex2jar.bat"
	JD_GUI = WORK_DIR + "/jd-gui/jd-gui.exe"
	JEB_EXE = WORK_DIR + "/jeb225/bin/jeb.exe"
	JEB_JAR = WORK_DIR + "/jeb225/bin/cl/jeb.jar"

	JEBDECOMPILEALL_PY_PATH = WORK_DIR + "/jeb225/scripts/JEB2DecompileAll.py"
	decompileApk()
	# decompileLuaCodeZip()

	# targetDir = "E:/referprojects/DecompileToolScript/v3quick/bin/com.xq5.ncmj_6.4_64/assets"
	# outputdir = "E:/referprojects/DecompileToolScript/v3quick/bin/com.xq5.ncmj_6.4_64/ouput"
	# key = "2dxLua"
	# sign = "XXTEA"
	
	# key = fixKeyLength(key)
	# decodeDir(targetDir,key,sign,outputdir)


	# decompileLuac("E:/referprojects/texas_hall/assets/ouput/game", "E:/referprojects/texas_hall/assets/ouput/gameout")

	# fixAllLuaChsErrorCode("E:/referprojects/texas_hall/assets/ouput/gameout")

	# string = '1 adfa fa 2 fafsa 3 adfaf'
	# print re.sub(r'(^|\b)[1-3]($|\b)', replace, string)