sudo yum update
sudo yum install gcc gcc-c++ kernel-devel
wget http://ftp.gnu.org/gnu/parallel/parallel-latest.tar.bz2
tar jxf parallel-latest.tar.bz2
rm parallel-latest.tar.bz2
cd parallel-20181022/
./configure
make
sudo make install
sudo ldconfig
sudo yum install ImageMagick ImageMagick-devel
sudo yum -y install automake autoconf libtool zlib-devel libjpeg-devel giflib libtiff-devel libwebp libwebp-devel libicu-devel openjpeg-devel cairo-devel
wget http://www.leptonica.com/source/leptonica-1.73.tar.gz
tar xzvf leptonica-1.73.tar.gz
rm leptonica-1.73.tar.gz
cd leptonica-1.73/
./configure
make
sudo make install
cd
wget https://github.com/tesseract-ocr/tesseract/archive/3.04.01.tar.gz
mv 3.04.01.tar.gz tesseract-3.04.01.tar.gz
tar xzvf tesseract-3.04.01.tar.gz
cd tesseract-3.04.01/
./autogen.sh
./configure
make
sudo make install
sudo ldconfig
wget https://sourceforge.net/projects/tesseract-ocr-alt/files/tesseract-ocr-3.02.eng.tar.gz
tar xzvf tesseract-ocr-3.02.eng.tar.gz
rm tesseract-ocr-3.02.eng.tar.gz
sudo mv tesseract-ocr/ /usr/share/
export TESSDATA_PREFIX=/usr/share/tesseract-ocr/tessdata
wget https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs920/ghostscript-9.20.tar.gz
tar xzvf ghostscript-9.20.tar.gz
rm xzvf ghostscript-9.20.tar.gz
cd ghostscript-9.20/
./autogen.sh
./configure
make
sudo make install
