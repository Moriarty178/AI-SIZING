package com.example.sizing.dto;

import lombok.Data;

@Data
public class SendNotificationRequest {
    private String projectId;
    private String recipientUserId;
    private String phoneNumber;
    private String messageType;
    private String messageContent;
    private String projectName;
}