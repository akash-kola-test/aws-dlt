#!/bin/bash

UUID=$(cat /proc/sys/kernel/random/uuid)
echo "S3_BUCKET:: ${S3_BUCKET}"
echo "TEST_ID:: ${TEST_ID}"
echo "PREFIX:: ${PREFIX}"
echo "UUID:: ${UUID}"
echo "AWS_REGION:: ${REGION}"

echo "Download test scenario"
aws s3 cp s3://$S3_BUCKET/test-scenarios/$TEST_ID-$AWS_REGION.json test.json --region $AWS_REGION

LOG_FILE="jmeter.log"
OUT_FILE="jmeter.out"
ERR_FILE="jmeter.err"
KPI_EXT="jtl"
EXT="jmx"

echo "Downloading test file"
aws s3 cp s3://$S3_BUCKET/public/test-scenarios/jmeter/$TEST_ID.$EXT ./ --region $AWS_REGION

echo "Running test"
stdbuf -i0 -o0 -e0 bzt test.json -o modules.console.disable=true | stdbuf -i0 -o0 -e0 tee -a result.tmp | sed -u -e "s|^|$TEST_ID|"

echo "Uploading results, bzt log, and JMeter log, out, and err files"
aws s3 cp /tmp/artifacts/results.xml s3://$S3_BUCKET/results/${TEST_ID}/${PREFIX}-${UUID}-${AWS_REGION}.xml --region $AWS_REGION
aws s3 cp /tmp/artifacts/bzt.log s3://$S3_BUCKET/results/${TEST_ID}/bzt-${PREFIX}-${UUID}-${AWS_REGION}.log --region $AWS_REGION
aws s3 cp /tmp/artifacts/$LOG_FILE s3://$S3_BUCKET/results/${TEST_ID}/${TEST_TYPE}-${PREFIX}-${UUID}-${AWS_REGION}.log --region $AWS_REGION
aws s3 cp /tmp/artifacts/$OUT_FILE s3://$S3_BUCKET/results/${TEST_ID}/${TEST_TYPE}-${PREFIX}-${UUID}-${AWS_REGION}.out --region $AWS_REGION
aws s3 cp /tmp/artifacts/$ERR_FILE s3://$S3_BUCKET/results/${TEST_ID}/${TEST_TYPE}-${PREFIX}-${UUID}-${AWS_REGION}.err --region $AWS_REGION
aws s3 cp /tmp/artifacts/kpi.${KPI_EXT} s3://$S3_BUCKET/results/${TEST_ID}/kpi-${PREFIX}-${UUID}-${AWS_REGION}.${KPI_EXT} --region $AWS_REGION
