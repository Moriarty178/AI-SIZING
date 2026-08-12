package com.example.sizing.service;

import com.example.sizing.model.Notification.NotificationStatus;
import com.example.sizing.repository.NotificationRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.util.UriComponentsBuilder;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

@Service
public class SmsDispatcher {
    private static final Logger log = LoggerFactory.getLogger(SmsDispatcher.class);

    private static final int MAX_RETRIES = 3;
    private static final long RETRY_DELAY_MS = 5000;

    private final NotificationRepository notificationRepository;
    private final RestTemplate restTemplate;

    @Value("${sms.server-url}")
    private String smsServerUrl;

    public SmsDispatcher(NotificationRepository notificationRepository, RestTemplate restTemplate) {
        this.notificationRepository = notificationRepository;
        this.restTemplate = restTemplate;
    }

    @Async("smsExecutor")
    public void sendSmsWithRetry(String notificationId, String phoneNumber, String message) {
        sendSmsWithRetryInternal(notificationId, phoneNumber, message, 0);
    }

    public void sendSmsWithRetrySync(String notificationId, String phoneNumber, String message) {
        sendSmsWithRetryInternal(notificationId, phoneNumber, message, 0);
    }

    private void sendSmsWithRetryInternal(String notificationId, String phoneNumber, String message, int attempt) {
        log.info("[SMS] sendSmsWithRetry: notificationId={}, phone={}, attempt={}/{}",
                notificationId, phoneNumber, attempt + 1, MAX_RETRIES);

        URI url;
        try {
            // Strip placeholder query params from config — keep only the base path
            String baseUrl = smsServerUrl.replaceFirst("\\?.*", "");
            url = UriComponentsBuilder
                    .fromHttpUrl(baseUrl)
                    .queryParam("message", message)
                    .queryParam("phone", phoneNumber)
                    .encode(StandardCharsets.UTF_8)
                    .build()
                    .toUri();
        } catch (Exception ex) {
            log.error("[SMS] Failed to build URL: smsServerUrl='{}', message='{}', phone='{}'",
                    smsServerUrl, message, phoneNumber, ex);
            updateNotificationStatus(notificationId, NotificationStatus.FAILED,
                    "Failed to build SMS URL: " + ex.getMessage());
            return;
        }
        log.info("[SMS] sendSmsWithRetry: constructed url='{}'", url);

        try {
            log.info("[SMS] Calling SMS server for notification {}...", notificationId);
            var response = restTemplate.getForEntity(url, String.class);
            String body = response.getBody();
            int statusCode = response.getStatusCode().value();
            log.info("[SMS] SMS server response: notificationId={}, status={}, body='{}'",
                    notificationId, statusCode, body);

            boolean serverReportedSuccess = statusCode >= 200 && statusCode < 300
                    && body != null && !body.isBlank()
                    && !body.toLowerCase().contains("lỗi")
                    && !body.toLowerCase().contains("error")
                    && !body.toLowerCase().contains("không")
                    && !body.toLowerCase().contains("fail");

            if (serverReportedSuccess) {
                updateNotificationStatus(notificationId, NotificationStatus.SENT, null);
                log.info("[SMS] SUCCESS: notificationId={} sent to {}", notificationId, phoneNumber);
            } else {
                updateNotificationStatus(notificationId, NotificationStatus.FAILED,
                        String.format("SMS server returned error. Status: %d, Body: %s", statusCode, body));
                log.error("[SMS] FAIL (server error): notificationId={}, status={}, body='{}'",
                        notificationId, statusCode, body);
            }
        } catch (RestClientException e) {
            log.error("[SMS] FAIL (connection error): notificationId={}, phone={}, url={}, error={}",
                    notificationId, phoneNumber, url, e.getMessage());

            if (attempt + 1 < MAX_RETRIES) {
                int currentRetry = incrementRetryCount(notificationId);
                long delay = RETRY_DELAY_MS * (long) Math.pow(2, currentRetry - 1);
                final int nextAttempt = attempt + 1;
                Executors.newSingleThreadScheduledExecutor()
                        .schedule(() -> sendSmsWithRetryInternal(notificationId, phoneNumber, message, nextAttempt),
                                delay, TimeUnit.MILLISECONDS);
                log.info("[SMS] Scheduling retry {}/{} for notificationId={} in {}ms",
                        nextAttempt + 1, MAX_RETRIES, notificationId, delay);
            } else {
                updateNotificationStatus(notificationId, NotificationStatus.FAILED,
                        String.format("Retries exhausted (%d attempts). Last error: %s | URL: %s",
                                MAX_RETRIES, e.getMessage(), url));
                log.error("[SMS] PERMANENT FAIL: notificationId={} after {} attempts", notificationId, MAX_RETRIES);
            }
        }
    }

    @Transactional
    public void updateNotificationStatus(String notificationId, NotificationStatus status, String errorMessage) {
        notificationRepository.findById(notificationId).ifPresent(n -> {
            n.setStatus(status);
            if (status == NotificationStatus.SENT) {
                n.setSentAt(LocalDateTime.now());
            }
            if (errorMessage != null) {
                n.setErrorMessage(errorMessage);
            }
            notificationRepository.save(n);
            log.info("[SMS] updateNotificationStatus: notificationId={}, status={}", notificationId, status);
        });
    }

    @Transactional
    public int incrementRetryCount(String notificationId) {
        return notificationRepository.findById(notificationId)
                .map(n -> {
                    int newCount = (n.getRetryCount() != null ? n.getRetryCount() : 0) + 1;
                    n.setRetryCount(newCount);
                    notificationRepository.save(n);
                    return newCount;
                })
                .orElse(0);
    }
}