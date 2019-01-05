import jwt
import time

iat = time.time()
exp = iat + 3600
payload = {'iss': '*******************************43.iam.gserviceaccount.com',
           'sub': '********************************3.iam.gserviceaccount.com',
           'aud': 'https://www.googleapis.com/oauth2/v4/token',
           'scope':'https://www.googleapis.com/auth/blogger',
           'iat': iat,
           'exp': exp}
additional_headers = {'kid': '*********************************d40f2b8'}
signed_jwt = jwt.encode(payload, '-----BEGIN PRIVATE KEY-----\n**********************************************************************************************************************************************************************************************************************************************************************************************************KKGffGLELuCknFQW6bDLxWxzEpm9Ia\n/8fwGyE1NRysNnRImEJ+IxYF+KAb/BPTJf0PGdzWCqG4hd9Gc7XS/oLOY2jk0Gwc\nWYkOiuBdAgMBAAECgf8fZXtSBzbAIDcOpqMTW77yPEX7xUEnyL1KRDhZaoN+DW0Z\n0aJXOSfXHDJQxdllLAGDXppY6PBN/rLKxtY1uMwnUdC4yYbHQjeBiH7nfgo/+Yyh\nsHiUQTuepPlMQq29HpIdE4He6hAcxvdLUJ6nlcSzk3Xa64jXbWi4a+UH8TokycNN\nELZJkkyrvlyeuH4XZ+v/RT++15AFp5VZX/X/TBha0xYwjI09wwMfPDySXwXu36I6\nmaMmwt2wMonIoNQiH6dK6D/NgnIllq1Kx8pMIVowQsTdNomGQ/pYUODeAmpaBCCU\nT3o+PIYmNZEudmQv8ZR5eAcxXOs1c8JfP319o+kCgYEA5mu/03VbHlzHoxWRNby4\naZx16QHXT9SqDfbRksaWSKSAZKw7wguVkGE28uunig81mE5LGWIQ5tIPPwQ/I3E8\nnRdGx/6E4ADvxiewJMSk1UAx2k0oN7Ss9AWLQx5AdW3LlEkAT6XMwUXjXZ/j+HjL\nPRjK2iTFxjBTj6jXtyiGqzUCgYEAuRMpiLxdtValZyabxsWNSct20NrGNix98sZh\nvl41aQuxVKKc2XiJ1cG64G/j3QNZ/zQr4Byi1tvmwbEzV1hAT/gtMZKTPG7KKcPJ\nO0u30uMrRwOgqrzCLLla8xgQ3SiVayMENxNGYnhd0+4Hplcnt4DoCfXMy3GGUMhc\nFZsLXY********************************************************************************************************************************************************************************************************************************P+3WBLjoVTHLgZ5jBr6Rh/t6Jfms4GjI\nri6DvBJEPFtkOCJ6/qMUdIBwx4Apmc2b2Iut4lDTpqxkGy4HNAc1vfyehIFbCjS9\nvlY8ZpY9MZkBskjYxgvhsKkua+5PfE9HyTs6qQKBgQCWDzNamlYGr1Xgpv1eTump\nDqjFj6IOuOrlr8KBiyxWlMaRN6Tn8z9iRjfyZ+35DRC65MEvcMBWwxYzV5TXIPVW\nzm2yUXH************************************************************************************n-----END PRIVATE KEY-----\n',headers=additional_headers,
                       algorithm='RS256')
print(signed_jwt) 
