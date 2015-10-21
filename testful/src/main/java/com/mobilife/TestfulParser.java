package com.mobilife;

import com.atlassian.bamboo.build.test.TestCollationService;
import com.atlassian.bamboo.task.TaskContext;
import com.atlassian.bamboo.task.TaskException;
import com.atlassian.bamboo.task.TaskResult;
import com.atlassian.bamboo.task.TaskResultBuilder;
import com.atlassian.bamboo.task.TaskType;

public class TestfulParser implements TaskType
{
    private final TestCollationService testCollationService;

    public TestfulParser(TestCollationService testCollationService)
    {
        this.testCollationService = testCollationService;
    }

    public TaskResult execute(TaskContext taskContext) throws TaskException
    {
        TaskResultBuilder taskResultBuilder = TaskResultBuilder.create(taskContext);

        final String testPattern = taskContext.getConfigurationMap().get("testPattern");
        
        testCollationService.collateTestResults(taskContext, testPattern, new TestfulResultCollector());

        return taskResultBuilder.checkTestFailures().build();
    }
}