PYTHON = python3
INSTALL_DIR = /usr/local/bin
PROGRAM_NAME = Alderys
SCRIPT_NAME = main.py

all: build install

build:
	@echo "building the executable"
	$(PYTHON) -m PyInstaller --onefile --name $(PROGRAM_NAME) $(SCRIPT_NAME)
	@echo "done. executable is ready."

install:
	@echo "installing to $(INSTALL_DIR)"
	sudo cp dist/$(PROGRAM_NAME) $(INSTALL_DIR)/$(PROGRAM_NAME)
	sudo chmod +x $(INSTALL_DIR)/$(PROGRAM_NAME)
	@echo "all set run '$(PROGRAM_NAME)' from anywhere"
  @cd && mkdir .icon && mkdir aldernys
  @cp ~/bin.png .icon/aldernys/

uninstall:
	@echo "uninstalling"
	sudo rm -f $(INSTALL_DIR)/$(PROGRAM_NAME)
	@echo "gone. nothing left."

clean:
	@echo "cleaning up"
	rm -rf build dist $(PROGRAM_NAME).spec
	@echo "clean"

.PHONY: all build install uninstall clean
