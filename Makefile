PYINSTALLER=pyinstaller
APPNAME=aldernys-fm
ICON=system-file-manager
DESKTOP=aldernys-fm.desktop

build:
	$(PYINSTALLER) --onefile --windowed --name $(APPNAME) --icon $(ICON) main.py

install:
	cp dist/$(APPNAME) /usr/local/bin/
	cp $(DESKTOP) /usr/share/applications/
	chmod +x /usr/local/bin/$(APPNAME)

uninstall:
	rm -f /usr/local/bin/$(APPNAME)
	rm -f /usr/share/applications/$(DESKTOP)

clean:
	rm -rf build dist $(APPNAME).spec
