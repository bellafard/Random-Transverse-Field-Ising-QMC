TEXFILE=manuscript
FIGURESDIR=.
FIGURES=$(wildcard $(FIGURESDIR)/*.pdf) $(wildcard $(FIGURESDIR)/*.eps)
INPUTS=$(wildcard *.tex)

all: $(TEXFILE).pdf

$(TEXFILE).pdf: $(TEXFILE).tex $(FIGURESDIR) $(INPUTS)
	/usr/texbin/pdflatex $(TEXFILE) > /dev/null

	@if(grep "Citation" $(TEXFILE).log > /dev/null);\
	then \
		bibtex $(TEXFILE) > /dev/null;\
		pdflatex $(TEXFILE) > /dev/null;\
	fi

	@if(grep "Rerun" $(TEXFILE).log > /dev/null);\
	then \
		pdflatex $(TEXFILE) > /dev/null;\
	fi

read:
	@if [ -f ~/.macBox ];then \
		Open -a Skim $(TEXFILE).pdf; \
	else \
		gvfs-open $(TEXFILE).pdf; \
	fi

clean:
	rm -f $(TEXFILE).ps $(TEXFILE).log $(TEXFILE).aux $(TEXFILE).out $(TEXFILE).dvi $(TEXFILE).bbl $(TEXFILE)Notes.bib $(TEXFILE).blg $(TEXFILE).toc $(FIGURESDIR)/*-eps-converted-to.pdf

tar: clean
	tar cvzf $(TEXFILE).tgz $(INPUTS) $(FIGURES) $(TEXFILE).pdf makefile

archive: clean
	tar cvzf `date +%Y%m%d`$(TEXFILE).tgz $(INPUTS) $(FIGURES) makefile
