#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import binascii
import struct
import errno

_DELTA = 0x9E3779B9  

def _long2str(v, w):  
    n = (len(v) - 1) << 2  
    if w:  
        m = v[-1]  
        if (m < n - 3) or (m > n): return ''  
        n = m  
    s = struct.pack('<%iL' % len(v), *v)  
    return s[0:n] if w else s  
  
def _str2long(s, w):  
    n = len(s)  
    m = (4 - (n & 3) & 3) + n  
    s = s.ljust(m, "\0")  
    v = list(struct.unpack('<%iL' % (m >> 2), s))  
    if w: v.append(n)  
    return v  
  
def encrypt(str, key):  
    if str == '': return str  
    v = _str2long(str, True)  
    k = _str2long(key.ljust(16, "\0"), False)  
    n = len(v) - 1  
    z = v[n]  
    y = v[0]  
    sum = 0  
    q = 6 + 52 // (n + 1)  
    while q > 0:  
        sum = (sum + _DELTA) & 0xffffffff  
        e = sum >> 2 & 3  
        for p in xrange(n):  
            y = v[p + 1]  
            v[p] = (v[p] + ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[p & 3 ^ e] ^ z))) & 0xffffffff  
            z = v[p]  
        y = v[0]  
        v[n] = (v[n] + ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[n & 3 ^ e] ^ z))) & 0xffffffff  
        z = v[n]  
        q -= 1  
    return _long2str(v, False)  
  
def decrypt(str, key):  
    if str == '': return str  
    v = _str2long(str, False)  
    k = _str2long(key.ljust(16, "\0"), False)  
    n = len(v) - 1  
    z = v[n]  
    y = v[0]  
    q = 6 + 52 // (n + 1)  
    sum = (q * _DELTA) & 0xffffffff  
    while (sum != 0):  
        e = sum >> 2 & 3  
        for p in xrange(n, 0, -1):  
            z = v[p - 1]  
            v[p] = (v[p] - ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[p & 3 ^ e] ^ z))) & 0xffffffff  
            y = v[p]  
        z = v[n]  
        v[0] = (v[0] - ((z >> 5 ^ y << 2) + (y >> 3 ^ z << 4) ^ (sum ^ y) + (k[0 & 3 ^ e] ^ z))) & 0xffffffff  
        y = v[0]  
        sum = (sum - _DELTA) & 0xffffffff  
    return _long2str(v, True) 

def readFile(filePath):
    file = open(filePath,'rb')
    text = file.read()
    file.close()
    return text

def writeFile(filePath, text):    
    file = open(filePath,'wb') 
    file.write(text)
    file.close()

# 获取文件夹路径下所有文件
def getAllFiles(path, prefix, files = []):
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

# 修正key值为16bit
def fixKeyLength(key):
    if len(key) < 16:
        key = key + "\0"*(16 - len(key))
    return key

# xxtea加密
def encodeXXTEA(rootDir, filePath, key, sign, outputDir):
    data = readFile(rootDir + "/" + filePath)
    ciphertext = encrypt(data, key)
    ciphertext = key + ciphertext
    filename = os.path.splitext(filePath)[0]
    writeFile(outputDir + "/" + filename + ".luac", ciphertext)

# 加密lua
def encodeLua(dirPath, key, sign, outputDir)
    key = fixKeyLength(key)
    fileList = getAllFiles(dirPath, '')
    copydir_p(dirPath, outputDir)
    for file in fileList:
        if file[-4:] == '.lua' or file[-5:] == '.luac':
            encodeXXTEA(dirPath, file, key, sign, outputDir)

# xxtea解密
def decodeXXTEA(rootDir, filePath, key, sign, outputDir):
    data = readFile(rootDir + "/" + filePath)
    if data[:len(sign)] == sign:
        luaData = data[len(sign):]
        plainText = decrypt(luaData, key)
        filename = os.path.splitext(filePath)[0]
        writeFile(outputDir + "/" + filename + ".lua", plainText)

# 解密lua
def decodeLua(dirPath, key, sign, outputDir):
    key = fixKeyLength(key)
    fileList = getAllFiles(dirPath, '')
    copydir_p(dirPath, outputDir)
    for file in fileList:
        if file[-4:] == '.lua' or file[-5:] == '.luac':
            decodeXXTEA(dirPath, file, key, sign, outputDir)


if __name__ == "__main__":
    targetDir = "E:/svnprojs/FantasySports/client/trunk/publish/test"
    outputDir = "E:/svnprojs/FantasySports/client/trunk/publish/ouput"
    key = "ZWFucmFuMjAxNw=="
    sign = "qanfan.cn"
    decodeLua(targetDir, key, sign, outputDir)
    print "decode ok"