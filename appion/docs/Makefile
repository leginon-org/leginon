# -----------------------------------------
# Makefile for appion documentation
# uses: http://txt2tags.sf.net
# -----------------------------------------

DATE := '$(shell date +"%B %d, %Y")'
SVNREV := 'r$(shell svnversion -n .)'
IMGDIR := -a icons -a iconsdir=/usr/share/asciidoc/images/icons/
ASCIIOPTS := -a revision=${SVNREV} -a date=${DATE}  -a compact --verbose --section-numbers

all: clean ahtml pdf gwiki

clean:
	rm -fv *~ *.log *.aux *.gwiki *.tex *.html *.pdf *.fo *.asciidoc

# -----------------------------------------
# Txt2Tags
# -----------------------------------------

thtml: INSTALL.txt
	echo "...creating appion install manual for LaTeX..."
	txt2tags --toc --infile=INSTALL.txt --target=html --outfile=INSTALL.html

asciidoc: INSTALL.txt
	echo "...creating appion install manual for LaTeX..."
	txt2tags --toc --infile=INSTALL.txt --target=asciidoc --outfile=INSTALL.asciidoc

latex: INSTALL.txt
	echo "...creating appion install manual for LaTeX..."
	txt2tags --toc --enum-title --infile=INSTALL.txt --target=tex --outfile=INSTALL.tex
	pdflatex INSTALL.tex
	rm -fv *.aux

gwiki: INSTALL.txt
	echo "...creating appion install manual for Google Wiki..."
	txt2tags --toc --enum-title --infile=INSTALL.txt --target=gwiki --outfile=INSTALL.gwiki

# -----------------------------------------
# AsciiDoc
# -----------------------------------------

docbook: INSTALL.txt asciidoc
	echo "...creating appion install manual for DocBook..."
	asciidoc ${ASCIIOPTS} --backend=docbook --out-file=INSTALL.xml INSTALL.asciidoc

ahtml: INSTALL.txt asciidoc
	echo "...creating appion install manual for HTML..."
	asciidoc ${ASCIIOPTS} -a toc ${IMGDIR} --backend=xhtml11 --out-file=INSTALL.html INSTALL.asciidoc
	#txt2tags --infile=INSTALL.txt --target=html --outfile=INSTALL.html

pdf: INSTALL.txt docbook
	echo "...creating appion install manual for PDF..."
	dblatex INSTALL.xml
	rm -fv INSTALL.xml




