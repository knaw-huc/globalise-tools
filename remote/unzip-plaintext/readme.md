https://github.com/globalise-huygens/glob-portal-infomodel/issues/58#issuecomment-4690766031 

the plaintext files for the inventories are currently gzipped. Is it difficult to change this to unzipped? The reason I ask: the object store implements the content-range header, allowing the request of specific byte ranges. I think it's an interesting small experiment to see if that works fast for text sections.

