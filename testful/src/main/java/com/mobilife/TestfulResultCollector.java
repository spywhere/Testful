package com.mobilife;

import com.atlassian.bamboo.build.test.TestCollectionResult;
import com.atlassian.bamboo.build.test.TestCollectionResultBuilder;
import com.atlassian.bamboo.build.test.TestReportCollector;
import com.atlassian.bamboo.results.tests.TestResults;
import com.atlassian.bamboo.resultsummary.tests.TestState;
import com.google.common.collect.Lists;
import com.google.common.collect.Sets;
import com.google.common.io.Files;

import java.nio.charset.Charset;
import java.io.File;
import java.util.Collection;
import java.util.List;
import java.util.Set;

import org.apache.commons.lang3.StringUtils;

public class TestfulResultCollector implements TestReportCollector
{
    public TestCollectionResult collect(File file) throws Exception
    {
        TestCollectionResultBuilder builder = new TestCollectionResultBuilder();

        Collection<TestResults> successfulTestResults = Lists.newArrayList();
        Collection<TestResults> skippingTestResults = Lists.newArrayList();
        Collection<TestResults> failingTestResults = Lists.newArrayList();

        List<String> lines = Files.readLines(file, Charset.forName("UTF-8"));

        for (String line : lines)
        {
            String[] atoms = StringUtils.split(line, '|');
            String suiteName = atoms[0];
            String testName = atoms[1];
            String durationInSeconds = atoms[2];
            String status = atoms[3];

            Double duration = Double.parseDouble(durationInSeconds);

            TestResults testResults = new TestResults(suiteName, testName, duration.toString());
            if ("pass".equals(status))
            {
                testResults.setState(TestState.SUCCESS);
                successfulTestResults.add(testResults);
            }else if ("skip".equals(status))
            {
                testResults.setState(TestState.SKIPPED);
                skippingTestResults.add(testResults);
            }
            else
            {
                testResults.setState(TestState.FAILED);
                failingTestResults.add(testResults);
            }
        }

        return builder
        		.addSuccessfulTestResults(successfulTestResults)
        		.addSkippedTestResults(skippingTestResults)
                .addFailedTestResults(failingTestResults)
                .build();
    }

    public Set<String> getSupportedFileExtensions()
    {
        return Sets.newHashSet("testful"); // this will collect all *.result files
    }
}