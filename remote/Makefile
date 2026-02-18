all: help
SHELL=/bin/bash
.SECONDARY:
.DELETE_ON_ERROR:

OUT=work
PAGEXMLDIR=$(OUT)/pagexml
XMIDIR=$(OUT)/xmi
MANIFESTSDIR=data/manifests
ALL_INV=$(shell cat $(OUT)/inventorynumbers.lst)
COMMIT=2026.02.16

# gate task to limit parallelism
.PHONY: hucdrive-gate
.NOTPARALLEL: hucdrive-gate
hucdrive-gate:
	@:

.PHONY: check-ssh
check-ssh:
	@if [ -z "$$SSHUSER" ]; then \
		echo "SSHUSER is not set: user for hucdrive.huc.knaw.nl"; \
		exit 1; \
	fi
	@if [ -z "$$SSHPASS" ]; then \
		echo "SSHPASS is not set: password for SSHUSER"; \
		exit 1; \
	fi

.make/:
	mkdir -p $@

$(OUT)/inventorynumbers.lst: | data/xmicas/
	/bin/ls data/xmicas/ | sed -e 's/.zip//' | sort -n > $@

.make/init: $(OUT)/inventorynumbers.lst | .make/
	cp pyproject.toml pyproject.toml.bak
	grep -v Users pyproject.toml.bak > pyproject.toml
	poetry install
	mv inventory2timespan.json document_data.json typesystem.xml data/
	@touch $@

.PHONY: init
init: .make/init

data/pagexml/:
	mkdir -p $@

data/pagexml/%.zip: REMOTE_SUFFIX = pagexml

data/xmicas/%.zip:  REMOTE_SUFFIX = xmi

data/%/%.zip: | hucdrive-gate check-ssh data/%/
	sshpass -e scp -P 2222 \
	  $(SSHUSER)@hucdrive.huc.knaw.nl:globalise/$*-$(REMOTE_SUFFIX).zip \
	  $@

.make/pagexml-%: data/pagexml/%.zip | .make/
	@mkdir -p $(PAGEXMLDIR)
	unzip -o --qq -j $< -d $(PAGEXMLDIR)/$*/
	@touch $@

data/xmicas/:
	mkdir -p $@

.make/xmicas-%: data/xmicas/%.zip | .make/
	@mkdir -p $(XMIDIR)
	unzip -o -qq -j $< -d $(XMIDIR)/$*
	@touch $@

.make/annotation-pages-%: .make/pagexml-% | .make/
	@touch $@

data/typesystem.xml:
	@echo "missing file: data/typesystem.xml"

.make/combined-%: .make/init scripts/gt-create-annotation-lists-for-inventory-number.sh .make/xmicas-% data/typesystem.xml .make/pagexml-%
	./scripts/gt-create-annotation-lists-for-inventory-number.sh $* && rm -rf {$(PAGEXMLDIR),$(XMIDIR)}/$*/ .make/{pagexml,xmicas}-$*
	@touch $@

$(OUT)/annotation-lists/:
	mkdir -p $@

$(OUT)/annotation-lists/%.zip: .make/combined-% | $(OUT)/annotation-lists/
	cd $(OUT)/$*/ && zip -qrm ../annotation-lists/$*.zip {entities,transcriptions}/*.json && cd .. && find $* -depth -empty -delete
	
$(OUT)/inv-done.lst:
	@touch $@

$(OUT)/inv-done-sorted.lst: $(OUT)/inv-done.lst
	sort -u $(OUT)/inv-done.lst | sort -n > $@

$(OUT)/inv-todo.lst: $(OUT)/inv-done-sorted.lst $(OUT)/inventorynumbers.lst
	#diff --suppress-common-lines --strip-trailing-cr --minimal $(OUT)/inventorynumbers.lst $(OUT)/inv-done-sorted.lst | grep "<" | sed -e "s/< //" > $@
	diff -wB work/inventorynumbers.lst work/inv-done-sorted.lst | grep "^-" | grep -v "lst" | sed -e "s/^-//" | sort -u | sort -n > $@

annotation-lists-%: $(OUT)/annotation-lists/%.zip | hucdrive-gate
#	$(MAKE) $(OUT)/annotation-lists/$*.zip
#	sshpass -e scp -P 2222 $(OUT)/annotation-lists/$*.zip ${SSHUSER}@hucdrive.huc.knaw.nl:annotationlists/$*-annotation-lists.zip && rm $(OUT)/annotation-lists/$*.zip
	mv $(OUT)/annotation-lists/$*.zip $(OUT)/annotation-lists/$*-annotation-lists.zip

.PHONY: all-annotation-lists
all-annotation-lists: $(OUT)/inventorynumbers.lst $(addprefix annotation-lists-,$(ALL_INV))

upload-%: $(OUT)/annotation-lists/%-annotation-lists.zip
	mkdir $(OUT)/$*/
	cd $(OUT)/$*/ && unzip -o ../annotation-lists/$*-annotation-lists.zip
	@echo "uploading annotation lists for $* ..."
	@echo "done, cleaning up ..."
	#rm -rf $(OUT)/$*/

.PHONY: upload-all
upload-all: scripts/gt-upload-all-annotation-lists.sh
	./scripts/gt-upload-all-annotation-lists.sh

.PHONY: help
help:
	@echo "available make targets:"
	@echo "  init                     - set up the environment for the scripts to run in"
	@echo "  annotation-lists-<invnr> - generate entities and transcription annotation pages for the given inventory number"
	@echo "  all-annotation-lists     - generate all entities and transcription annotation pages"
	@echo "  upload-<invnr>           - upload the annotationlists of the given inventory number to the object store"
	@echo "  upload-all               - upload all annotationlists to the object store"
