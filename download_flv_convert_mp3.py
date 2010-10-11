import httplib
import urllib
import unicodedata
import re
import sys
import os
import subprocess
import win32com.client
import youtube_dl

YOUTUBE_RE1 = r'http:\/\/www\.youtube\.com\/watch(\?|#!|#)v(ideos)?=([\w-]+)'
YOUTUBE_RE2 = r'http:\/\/www\.youtube\.com\/user\/\w+#(.\/)+([\w-]+)'
WORKING_DIR = "c:\\youtube\\"

python_exe = 'c:/python26/python.exe'
youtube_dl_py = 'c:/youtube/youtube_dl.py'

skipDownload = False
convertMP3 = True
convertMP4 = True

logFile = None

if len(sys.argv) != 2:
    print "Wrong number of arguments.  Exiting..."
    sys.exit(1)
        
youtubeURL = sys.argv[1]

def CreateLog(video_id):
    global logFile
    logFilename = os.path.join(WORKING_DIR, video_id + "_log.txt")
    logFile = open(logFilename, 'wt')
    print "create", logFile
    
def Log(message):
    print "log", logFile
    logFile.write(message)
    logFile.write('\n')
    logFile.flush()

def CloseLog():
    logFile.close()
        
def GetYoutubeVideoInfo(videoID,eurl=None):
	'''
	Taken from http://geniusofevil.wordpress.com/2009/04/30/howto-get-direct-youtube-video-flv-url/
	
	Return direct URL to video and dictionary containing additional info
	>> url,info = GetYoutubeVideoInfo("tmFbteHdiSw")
	>>
	'''
	if not eurl:
		params = urllib.urlencode({'video_id':videoID})
	else :
		params = urllib.urlencode({'video_id':videoID, 'eurl':eurl})
	Log("GetYoutubeVideoInfo params: %s\n" % params)

	conn = httplib.HTTPConnection("www.youtube.com")
	conn.request("GET","/get_video_info?&%s"%params)
	response = conn.getresponse()
	Log("GetYoutubeVideoInfo response: %s\n" % response)
	data = response.read()
	Log("GetYoutubeVideoInfo data: %s\n" % data)
	video_info = dict((k,urllib.unquote_plus(v)) for k,v in (nvp.split('=') for nvp in data.split('&')))
	request_parms = '/get_video?video_id=%s&t=%s' %( video_info['video_id'],video_info['token'])
	Log("GetYoutubeVideoInfo request_parms: %s\n" % request_parms)
	conn.request('GET', request_parms)
	response = conn.getresponse()
	Log("GetYoutubeVideoInfo response: %s\n" % response)
	direct_url = response.getheader('location')
	Log("GetYoutubeVideoInfo direct_url: %s\n" % direct_url)
	return direct_url,video_info 

def RegexYoutubeURL(pattern, url):
    video_id = None
    video_id_match = re.match(pattern, url)
    
    if video_id_match:
        group_count = len(video_id_match.groups())
        if group_count > 0:
            video_id = video_id_match.groups()[group_count-1]

    return video_id
    
def GetYoutubeVideoIDFromURL(url):
    """
    Try matching multiple known youtube url patterns.
    """
    video_id = RegexYoutubeURL(YOUTUBE_RE1, url)

    if not video_id:
        video_id = RegexYoutubeURL(YOUTUBE_RE2, url)
        
    return video_id

def DownloadFLV(videoID):
    flvURL, flvInfo = GetYoutubeVideoInfo(videoID)
    Log("test URL: " + flvURL + "\n")
    Log("FLV INFO: " + str(flvInfo) + "\n")

    localFLV = os.path.join(WORKING_DIR, videoID + ".flv")
    if os.path.exists(localFLV) and (os.path.getsize(localFLV) > 0):
        Log("FLV %s already exists locally.  Skipping download\n" % localFLV)
        return flvInfo
    
    if not skipDownload:
        flvSource = urllib.urlopen(flvURL)
        Log("Opening URL: %s\n" % flvURL)

        flvDest = open(localFLV, 'wb')
        Log("Created local file: %s\n" % localFLV)
                        
        flvDest.write(flvSource.read())
        Log("Finished downloading flv\n")
                       
        flvDest.close()
        Log("Closed local FLV\n")

        flvSource.close()
        Log("Closed internet FLV\n")

    return flvInfo        

def slugify(value):
    """
    Taken from http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python/295466#295466
    
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)        

def ConvertFLVtoMP3(flvFile, mp3File):
    if os.path.exists(mp3File):
        Log("MP3 %s already exists locally.  Skipping conversion\n" % mp3File)
        return 0
    
    command = 'ffmpeg.exe -y -i "%s" -vn "%s"' % (flvFile, mp3File)
    Log( "Running command %s" % command )
    return os.system(command)
def ConvertFLVtoMP4(flvFile, mp4File):
    if os.path.exists(mp4File):
        Log("MP4 %s already exists locally.  Skipping conversion\n" % mp4File)
        return 0

    command = 'ffmpeg.exe -i "%s" -ar 22050 "%s"' % (flvFile, mp4File)
    Log( "Running command %s" % command )
    return os.system(command)

def OpeniTunes(filename):
    Log("Opening iTunes with %s\n" % filename)
    iTunes = win32com.client.gencache.EnsureDispatch("iTunes.Application")
    iTunes.PlayFile(filename)

def Main():
    youtubeID = GetYoutubeVideoIDFromURL(youtubeURL)
    if youtubeID == None:
         print "Unable to parse regex for url: %s\n" % (youtubeURL)
         sys.exit(1)

    os.chdir(WORKING_DIR)

    CreateLog(youtubeID)
    Log("Youtube Video ID: " + youtubeID + "\n")

    # Get vide title        
    process = subprocess.Popen([python_exe, youtube_dl_py, '-e', youtubeURL], shell=False, stdout=subprocess.PIPE)
    youtubeTitle = process.communicate()[0].strip()
    Log("Youtube Video Title: " + youtubeTitle + "\n")

    # Download flv
    Log( "Before dl" )
    subprocess.call("%s %s -lc %s" % (python_exe, youtube_dl_py, youtubeURL), shell=False)
    Log( "After dl" )
    # TODO: Check for errors    

    baseFilename = youtubeTitle + "-" + youtubeID 

    localFLV = os.path.join(WORKING_DIR, baseFilename+'.flv')
    localMP3 = os.path.join(WORKING_DIR, baseFilename+'.mp3')
    localMP4 = os.path.join(WORKING_DIR, baseFilename+'.mp4')
    Log("localFLV: " + localFLV + "\n")
    Log("localMP3: " + localMP3 + "\n")
    Log("localMP4: " + localMP4 + "\n")

    if convertMP4 and ConvertFLVtoMP4(localFLV, localMP4) == 0:
        OpeniTunes(localMP4)

    if convertMP3 and ConvertFLVtoMP3(localFLV, localMP3) == 0:
        OpeniTunes(localMP3)

    #CloseLog()                

Main()
