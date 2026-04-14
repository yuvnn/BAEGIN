package com.baegin.auth.service;

import com.slack.api.Slack;
import com.slack.api.methods.MethodsClient;
import com.slack.api.methods.response.conversations.ConversationsOpenResponse;
import com.slack.api.methods.response.users.UsersLookupByEmailResponse;
import org.springframework.stereotype.Service;

import java.util.logging.Logger;

@Service
public class SlackService {

    private static final Logger log = Logger.getLogger(SlackService.class.getName());

    private final String botToken = System.getenv("SLACK_BOT_TOKEN");

    public void sendOtp(String email, String code) {
        if (botToken == null || botToken.isBlank()) {
            log.warning("SLACK_BOT_TOKEN not set — OTP for " + email + " is: " + code);
            return;
        }
        try {
            Slack slack = Slack.getInstance();
            MethodsClient methods = slack.methods(botToken);

            UsersLookupByEmailResponse lookupResp = methods.usersLookupByEmail(
                    r -> r.email(email));
            if (!lookupResp.isOk()) {
                log.warning("Slack user lookup failed for " + email + ": " + lookupResp.getError());
                return;
            }
            String userId = lookupResp.getUser().getId();

            ConversationsOpenResponse openResp = methods.conversationsOpen(
                    r -> r.users(java.util.List.of(userId)));
            if (!openResp.isOk()) {
                log.warning("Slack DM open failed: " + openResp.getError());
                return;
            }
            String channelId = openResp.getChannel().getId();

            methods.chatPostMessage(r -> r
                    .channel(channelId)
                    .text("[BAEGIN] 인증 코드: *" + code + "* (5분 유효)"));

        } catch (Exception e) {
            log.warning("Slack send failed: " + e.getMessage());
        }
    }
}
