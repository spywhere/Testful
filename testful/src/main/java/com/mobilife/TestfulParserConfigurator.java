package com.mobilife;

import com.atlassian.bamboo.collections.ActionParametersMap;
import com.atlassian.bamboo.task.AbstractTaskConfigurator;
import com.atlassian.bamboo.task.TaskDefinition;
import com.atlassian.bamboo.task.TaskTestResultsSupport;
import com.atlassian.bamboo.v2.build.agent.capability.Requirement;
import com.atlassian.bamboo.utils.error.ErrorCollection;
import com.google.common.collect.ImmutableMap;
import com.google.common.collect.ImmutableSet;
import org.apache.commons.lang3.StringUtils;

import java.util.Collections;
import java.util.Map;
import java.util.Set;

public class TestfulParserConfigurator extends AbstractTaskConfigurator implements TaskTestResultsSupport
{
    public static final String PATTERN = "testPattern";

    protected static final Set<String> FIELDS_TO_COPY = ImmutableSet.<String>builder()
            .add(PATTERN)
            .build();
    protected static final Map<String, Object> DEFAULT_FIELD_VALUES = ImmutableMap.<String, Object>builder()
            .put(PATTERN, "results.testful")
            .build();
    
    @Override
    public Map<String, String> generateTaskConfigMap(ActionParametersMap params, TaskDefinition previousTaskDefinition)
    {
        final Map<String, String> map = super.generateTaskConfigMap(params, previousTaskDefinition);
        taskConfiguratorHelper.populateTaskConfigMapWithActionParameters(map, params, getFieldsToCopy());
        return map;
    }

    @Override
    public void populateContextForCreate(Map<String, Object> context)
    {
        super.populateContextForCreate(context);
        context.putAll(getDefaultFieldValues());
    }

    @Override
    public void populateContextForEdit(Map<String, Object> context, TaskDefinition taskDefinition)
    {
        super.populateContextForEdit(context, taskDefinition);
        taskConfiguratorHelper.populateContextWithConfiguration(context, taskDefinition, getFieldsToCopy());
    }
    
    @Override
    public void validate(ActionParametersMap params, ErrorCollection errorCollection)
    {
        super.validate(params, errorCollection);
        if (StringUtils.isBlank(params.getString(PATTERN)))
        {
            errorCollection.addError(PATTERN, "Test pattern cannot be empty");
        }
    }

    @Override
    public boolean taskProducesTestResults(TaskDefinition taskDefinition)
    {
        return true;
    }

    public Set<String> getFieldsToCopy()
    {
        return FIELDS_TO_COPY;
    }

    public Map<String, Object> getDefaultFieldValues()
    {
        return DEFAULT_FIELD_VALUES;
    }
}