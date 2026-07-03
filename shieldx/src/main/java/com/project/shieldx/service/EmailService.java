package com.project.shieldx.service;

import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class EmailService {

    private final JavaMailSender mailSender;

    public void sendOtpEmail(String to, String subject, String name, String otp) {
        try {
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper =
                    new MimeMessageHelper(message, true, "UTF-8");

            helper.setTo(to);
            helper.setSubject(subject);
            helper.setFrom("no-reply@shieldx.com");
            helper.setText(buildOtpHtml(name, otp), true);

            mailSender.send(message);
        } catch (Exception e) {
            throw new RuntimeException("Failed to send OTP email 💀", e);
        }
    }

    private String buildOtpHtml(String name, String otp) {
        return """
                 <!DOCTYPE html>
                        <html>
                        <head>
                          <meta charset="UTF-8">
                          <title>OTP Verification</title>
                        </head>
                        <body style="margin:0;padding:0;background-color:#f4f6f8;font-family:Arial,Helvetica,sans-serif;">
                
                          <table width="100%%" cellpadding="0" cellspacing="0">
                            <tr>
                              <td align="center" style="padding:40px 0;">
                
                                <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:10px;overflow:hidden;">
                
                                  <!-- HEADER -->
                                  <tr>
                                    <td style="background:#0f172a;padding:20px;text-align:center;">
                                      <span style="color:#ffffff;font-size:42px;font-weight:bold;">
                                        SHIELD<span style="color:#38bdf8;">X</span>
                                      </span>
                                    </td>
                                  </tr>
                
                                  <!-- TITLE -->
                                  <tr>
                                    <td style="background:#111827;color:#ffffff;text-align:center;padding:0px;">
                                      <h2 style="margin:0; font-size:22px;font-weight:600;">OTP Verification</h2>
                                      <p style="margin-top:10px;font-size:12px;color:#cbd5e1;">
                                        Secure access confirmation
                                      </p>
                                    </td>
                                  </tr>
                
                                  <!-- BODY -->
                                  <tr>
                                    <td style="padding:30px;color:#374151;">
                                      <p style="font-size:16px;">Hello <b>%s</b>,</p>
                
                                      <p style="font-size:15px;line-height:1.6;">
                                        We received a request to verify your identity.
                                        Please use the OTP below to continue.
                                      </p>
                
                                      <div style="margin:30px 0;text-align:center;">
                                       <span style="
                    display:inline-block;
                    font-size:30px;
                    letter-spacing:10px;
                    padding:15px 25px;
                    border: 3px solid  black; /* Added this line */
                    background:#f1f5f9;
                    color:#0f172a;
                    border-radius:8px;
                    font-weight:bold;
                ">
                    %s
                </span>
                                      </div>
                
                                      <p style="font-size:14px;">
                                        ⏱ This OTP is valid for <b>2 minutes</b>.
                                      </p>
                
                                      <p style="font-size:14px;color:#6b7280;">
                                        Do not share this OTP with anyone. ShieldX will never ask for it.
                                      </p>
                
                                      <p style="margin-top:30px;font-size:13px;color:#9ca3af;">
                                        If you did not request this, please ignore this email.
                                      </p>
                                    </td>
                                  </tr>
                
                                  <!-- FOOTER -->
                                  <tr>
                                    <td style="background:#0f172a;color:#cbd5e1;text-align:center;padding:20px;font-size:12px;">
                                      © 2025 ShieldX. All rights reserved.
                                    </td>
                                  </tr>
                
                                </table>
                
                              </td>
                            </tr>
                          </table>
                
                        </body>
                        </html>
        """.formatted(name, otp);
    }
}
