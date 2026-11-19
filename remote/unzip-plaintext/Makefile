../work/%/%.txt:
	curl -Ls --compressed https://id.globalise.nl/hdl:20.500.14722/inventory:$*.txt > $@

re-upload-plaintext-unzipped-%: ../work/%/%.txt
	s5cmd cp \
	  --content-type "text/plain;charset=UTF-8" \
	  $< \
	  s3://globalise-data/objects/inventory/$*.txt \
	  > /dev/null
	@echo "uploaded https://id.globalise.nl/hdl:20.500.14722/inventory:$*.txt"
