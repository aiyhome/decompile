#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import hashlib
import time
import json
import zipfile
import shutil
import re

DEBUG = True
VERSION_CODE = 1
VERSION_NAME = "1.0.0"
PROP_LUA_ENCRYPT_KEY= "qanfan2017"
PROP_LUA_ENCRYPT_SIGN="qanfan.cn"

VERSION_URL = "http://192.168.3.65/update/"
if DEBUG:
    timeStr = time.strftime("%Y%m%d%H%M%S",time.localtime(time.time()))
    VERSION_NAME = VERSION_NAME + "." + timeStr + "." + str(VERSION_CODE)
else:
    timeStr = time.strftime("%m%d",time.localtime(time.time()))
    VERSION_NAME = VERSION_NAME + "." + timeStr + "." + str(VERSION_CODE)


ManifestObj = {
    "packageUrl" : "%s" % VERSION_URL,
    "remoteManifestUrl" : "%s/version/project.manifest" % VERSION_URL,
    "remoteVersionUrl" : "%s/version/brief.manifest" % VERSION_URL,
    "version" : "%s" % VERSION_NAME,
    "engineVersion" : "3.15.1",
}
PROJ_ROOT_DIR = os.getcwd()
PUBLISH_DIR = os.getcwd() + "/publish/hotupdate"
MANIFEST_DIR = PUBLISH_DIR + "/version"
# 获取文件的md5值
def getFileMd5(filename):
    if not os.path.isfile(filename):
        return
    md5 = hashlib.md5()# create a md5 object
    f = file(filename,'rb')
    while True:
        b = f.read(8096)# get file content.
        if not b :
            break
        md5.update(b)#encrypt the file
    f.close()
    return md5.hexdigest()

# 把某一目录下的所有文件复制到指定目录中：
def copyFiles(sourceDir,  targetDir): 
    if sourceDir.find(".svn") > 0: 
        return 
    for file in os.listdir(sourceDir): 
        sourceFile = os.path.join(sourceDir,  file) 
        targetFile = os.path.join(targetDir,  file) 
        if os.path.isfile(sourceFile): 
            if not os.path.exists(targetDir):  
                os.makedirs(targetDir)  
            if not os.path.exists(targetFile) or(os.path.exists(targetFile) and (os.path.getsize(targetFile) != os.path.getsize(sourceFile))):  
                open(targetFile, "wb").write(open(sourceFile, "rb").read()) 
        if os.path.isdir(sourceFile): 
            First_Directory = False 
            copyFiles(sourceFile, targetFile)    
# 删除一级目录下的所有文件：
def removeFileInFirstDir(targetDir): 
    for file in os.listdir(targetDir): 
        targetFile = os.path.join(targetDir,  file) 
        if os.path.isfile(targetFile): 
            os.remove(targetFile)

# 删除文件夹下所有文件及文件夹
def removeAllFileAndDir(targetDir):         
    filelist=[]    
    filelist=os.listdir(targetDir)  
    for f in filelist:  
        filepath = os.path.join( targetDir, f )  
        if os.path.isfile(filepath):  
            os.remove(filepath)  
            print filepath+" removed!"  
        elif os.path.isdir(filepath):  
            shutil.rmtree(filepath,True)  
            print "dir "+filepath+" removed!"

# 删除文件夹下所有文件及文件夹（指定的后缀除外）
def removeAllFilesWithFilter(targetDir, filtername):
    filelist=[]    
    filelist=os.listdir(targetDir)  
    for f in filelist:  
        filepath = os.path.join( targetDir, f ) 
        if not filepath.endswith(filtername):
            if os.path.isfile(filepath):
                os.remove(filepath)  
                print filepath+" removed!"  
            elif os.path.isdir(filepath):  
                shutil.rmtree(filepath,True)  
                print "dir "+filepath+" removed!"

# 压缩文件夹
def zipDir(dirname,zipfilename):
    filelist = []
    if os.path.isfile(dirname):
        filelist.append(dirname)
    else :
        for root, dirs, files in os.walk(dirname):
            for name in files:
                filelist.append(os.path.join(root, name))
          
    zf = zipfile.ZipFile(zipfilename, "w", zipfile.ZIP_STORED,allowZip64=True)
    for tar in filelist:
        arcname = tar[len(dirname):]
        #print arcname
        zf.write(tar,arcname)
    zf.close()

# 遍历文件获取md5值
def walkMd5(path, prefix, assets):
    fl = os.listdir(path) # get what we have in the dir.
    for f in fl:
        if os.path.isdir(os.path.join(path,f)): # if is a dir.
            if prefix == '':
                walkMd5(os.path.join(path,f), f, assets)
            else:
                walkMd5(os.path.join(path,f), prefix + '/' + f, assets)
        else:
            md5 = getFileMd5(os.path.join(path,f))
            key = ''
            if prefix != '':
                key = prefix + '/' + f
            else:
                key = f

            assets[key] = {
                "md5": md5
            }

# base64编码
ALPHA_BASE='ABCDEFGHIJKLMNOPQRSTUVWabcXYZdefghijklmnopqrstuvwxyz0123456789+/' 
def base64Encode(string):
    out=''
    c=len(string)%3
    a=''.join(bin(ord(i)).replace('0b','').zfill(8) for i in string)
    if(c==1):
        a+='0000'
    if(c==2):
        a+='00'
    m=int(len(a)/6)
    for j in range(m):
        out+=ALPHA_BASE[int(a[j*6:j*6+6],2)]
    if(c==1):
        out+='=='
    if(c==2):
        out+='='
    return out

# 编译lua脚本
def luacompile(srcDir, dstDir):
    key = base64Encode(PROP_LUA_ENCRYPT_KEY)
    cmd = "cocos luacompile -s %s -d %s -e -k %s -b %s --disable-compile" % (srcDir, dstDir,key,PROP_LUA_ENCRYPT_SIGN)
    print(cmd)
    os.system(cmd)

# 同步修改android项目XXTEA的key和sign
def modifyXXTEAKeyAndSignInGradle():
    propFilePath = PROJ_ROOT_DIR + "/frameworks/runtime-src/proj.android-studio/gradle.properties"
    file = open(propFilePath, 'r+')
    newText = ''
    hasKey = False
    hasSign = False
    while 1:
        line = file.readline()
        if line:
            if line.startswith('#'):
                newText += line
            elif line.find("PROP_LUA_ENCRYPT_KEY=") != -1:
                newLine = re.sub("PROP_LUA_ENCRYPT_KEY=(\S*)", "PROP_LUA_ENCRYPT_KEY=%s" % base64Encode(PROP_LUA_ENCRYPT_KEY), line)
                newText += newLine
                hasKey = True
            elif line.find("PROP_LUA_ENCRYPT_SIGN=") != -1:
                newLine = re.sub("PROP_LUA_ENCRYPT_SIGN=(\S*)", "PROP_LUA_ENCRYPT_SIGN=%s" % PROP_LUA_ENCRYPT_SIGN, line)
                newText += newLine
                hasSign = True
            else:
                newText += line

        else:
            break
    if not hasKey:
        newText += "PROP_LUA_ENCRYPT_KEY=%s\n" % base64Encode(PROP_LUA_ENCRYPT_KEY)
    if not hasSign:        
        newText += "PROP_LUA_ENCRYPT_SIGN=%s\n" % PROP_LUA_ENCRYPT_SIGN
    file.truncate()
    file.seek(0)
    file.write(newText)
    file.close()

# 同步修改cpp代码里面XXTEA的key和sign
def modifyXXTEAKeyAndSignInCpp():
    cppFilePath = PROJ_ROOT_DIR + '/frameworks/runtime-src/Classes/AppDelegate.cpp'

    file = open(cppFilePath,'rb')
    allText = file.read()
    file.close()

    pos = allText.find('stack->setXXTEAKeyAndSign')
    left = allText.find('(',pos)
    right = allText.find(';',pos)
    word = str.format('("%s", strlen("%s"), "%s", strlen("%s"))' % (PROP_LUA_ENCRYPT_KEY,PROP_LUA_ENCRYPT_KEY,PROP_LUA_ENCRYPT_SIGN,PROP_LUA_ENCRYPT_SIGN))
    headText = allText[:left]
    tailText = allText[right - len(allText):]
    allText = headText + word + tailText

    file = open(cppFilePath,'wb') 
    file.write(allText)
    file.close()

if __name__ == "__main__":
    # modifyXXTEAKeyAndSignInGradle()
    # modifyXXTEAKeyAndSignInCpp()

    timeStr = time.strftime("%Y%m%d%H%M%S",time.localtime(time.time()))
    if not os.path.exists(PUBLISH_DIR):
        os.mkdir(PUBLISH_DIR)
    if not os.path.exists(MANIFEST_DIR):
        os.mkdir(MANIFEST_DIR)


    # 生成版本摘要文件
    data = ManifestObj
    with open(MANIFEST_DIR + '/brief.manifest', 'w') as f:
        json.dump(data, f, encoding="utf-8", sort_keys=True, indent=4)
        f.close()

    # 复制
    cpResDir = PUBLISH_DIR + "/res"
    removeAllFileAndDir(cpResDir)
    copyFiles(PROJ_ROOT_DIR + "/res", cpResDir)

    cpSrcDir = PUBLISH_DIR + "/" + "src"
    removeAllFileAndDir(cpSrcDir)
    # copyFiles(PROJ_ROOT_DIR + "/" + "src",cpSrcDir)
    luacompile(PROJ_ROOT_DIR + "/" + "src",cpSrcDir)

    codeZipFile = "src/code.zip"
    zipDir(PUBLISH_DIR + "/src", PUBLISH_DIR + "/" + codeZipFile)
    removeAllFilesWithFilter(cpSrcDir, ".zip")

    # 生成版本详细文件
    assets = {}
    walkMd5(PUBLISH_DIR + "/res", "res", assets)
    # print (assets)
    assets[codeZipFile] = {
        "md5": getFileMd5(PUBLISH_DIR + "/" + codeZipFile),
        "compressed": True
    }
    data["assets"] = assets
    data["searchPaths"] = []

    with open(MANIFEST_DIR + '/project.manifest', 'w') as f:
        json.dump(data, f, encoding="utf-8", sort_keys=True, indent=4)
        f.close()
    
    # 复制版本信息到当前项目中
    removeAllFileAndDir(PROJ_ROOT_DIR + "/version")
    copyFiles(MANIFEST_DIR, PROJ_ROOT_DIR + "/version")

    # 发布到服务器上
    removeAllFileAndDir("E:/www/update")
    copyFiles(PUBLISH_DIR, "E:/www/update")
    print 'generate version.manifest finish.'