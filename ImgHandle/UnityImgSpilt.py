#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pypng as png
import os
import sys

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

def png_spilt(filename, rgb_output_file, a_output_file):
	picture = png.Reader(filename)
	rgb_colors = []#get all alpha color
	alphas = []
	data = picture.asRGBA()
	for rowPixels in data[2]:
		rgb_row = []
		alpha_row = []
		for i in range(1, len(rowPixels)/4):
			ridx = (i - 1)*4
			rgb_row.append(rowPixels[ridx])
			rgb_row.append(rowPixels[ridx+1])
			rgb_row.append(rowPixels[ridx+2])

			aidx = ridx+3
			alpha_row.append(rowPixels[aidx])
			alpha_row.append(rowPixels[aidx])
			alpha_row.append(rowPixels[aidx])

		rgb_colors.append(rgb_row)
		alphas.append(alpha_row)
	png.from_array(rgb_colors, 'RGB').save(rgb_output_file)
	png.from_array(alphas, 'RGB').save(a_output_file)

def png_merge(rgb_filename, a_filename, output_file):
	pic_a =png.Reader(rgb_filename)
	rgba_colors = []
	rgb_data = pic_a.asRGBA()
	for rowPixels in rgb_data[2]:
		rgba_row = []
		for i in range(1, len(rowPixels)/4):
			ridx = (i - 1)*4
			rgba_row.append(rowPixels[ridx])
			rgba_row.append(rowPixels[ridx+1])
			rgba_row.append(rowPixels[ridx+2])
			rgba_row.append(0)		
		rgba_colors.append(rgba_row)

	pic_b =png.Reader(a_filename)
	a_data = pic_b.asRGBA()
	row = 0
	skip = False
	for rowPixels in a_data[2]:
		for i in range(1, len(rowPixels)/4):
			ridx = (i - 1)*4
			aidx = ridx + 3
			try:
				rgba_colors[row][aidx] = rowPixels[ridx]
			except Exception as e:
				skip = True
				print 'skip ' + rgb_filename + '\n'
				break
		if skip:
			break
		row = row + 1
	if not skip:
		png.from_array(rgba_colors, 'RGBA').save(output_file)

def getValidImgFileDict(path, prefix, dict):
	fl = os.listdir(path) # get what we have in the dir.
	for f in fl:
	    if os.path.isdir(os.path.join(path,f)): # if is a dir.
	        if prefix == '':
	            getValidImgFileDict(os.path.join(path,f), f, files)
	        else:
	            getValidImgFileDict(os.path.join(path,f), prefix + '/' + f, files)
	    else:
	        filename = ''
	        if prefix != '':
	            filename = prefix + '/' + f
	        else:
	            filename = f
	        dict[filename] = filename
	return dict

if __name__ == "__main__":
    # ===== parse args =====
	changeWordDir(curFileDir())
	WORK_DIR = os.getcwd()

	# png_spilt("input/BetUI.png", "output/BetUI2.png", "output/BetUI_Alpha2.png")
	# png_merge("output/BetUI.png", "output/BetUI_Alpha.png", "input/BetUI.png")
	filesDict = {}
	imgDir = WORK_DIR + "/../v3quick/bin/com.qqgame.happymj_6.9.73_69730/assets/output/Texture2D"
	filesDict = getValidImgFileDict(imgDir, '', filesDict)
	for key in filesDict:
		if not ("_Alpha" in key):
			info = os.path.splitext(key)
			key_alpha = info[0] + "_Alpha" + info[1]
			if filesDict.has_key(key_alpha):
				png_merge(imgDir + "/" + key, imgDir + "/" + key_alpha, imgDir + "/../Texture2D_Merge/" + key)
