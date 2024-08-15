#!/bin/bash

let count=0;
for f in $(ls ./tests-2/*.txt); do 
	./a.out <$f > ./tests-2/`basename $f .txt`.output; 
done;

for f in $(ls ./tests-2/*.output); do
	diff -Bw $f  ./tests-2/`basename $f .output`.txt.expected > ./tests-2/`basename $f .output`.diff;
done

for f in $(ls tests-2/*.diff); do
	echo "========================================================";
	echo "FILE:" `basename $f .output`;
	echo "========================================================";
	if [ -s $f ]; then
		cat ./tests-2/`basename $f .diff`.txt;
		echo "--------------------------------------------------------";
		cat $f
	else
		count=$((count+1));
		echo "NO ERRORS HERE!";
	fi
done

echo "$count / 12 tests passed!";

rm tests-2/*.output
rm tests-2/*.diff

