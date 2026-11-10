#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p build/classes build/test-classes

echo "Compiling main sources..."
javac -d build/classes src/main/java/com/yazan/kvstore/*.java

echo "Compiling test sources..."
javac -cp "build/classes:lib/junit-4.13.2.jar:lib/hamcrest-core-1.3.jar" \
      -d build/test-classes src/test/java/com/yazan/kvstore/*.java

echo "Running tests..."
java -cp "build/classes:build/test-classes:lib/junit-4.13.2.jar:lib/hamcrest-core-1.3.jar" \
     org.junit.runner.JUnitCore com.yazan.kvstore.KVStoreTest com.yazan.kvstore.KVHttpServerTest

echo ""
echo "To run the server: java -cp build/classes com.yazan.kvstore.KVHttpServer"
