import base64

class Crypto(object):
    
    def __init__(self,data):
        self.key = "*&*%$%^&(#)**^$&hdsgahgdsb"   # Secret key
        self.data = str(data)
        
    def encrypt(self):
        try:
            encoded_chars = []
            for i in range(len(self.data)):
                key_c = self.key[i % len(self.key)]
                encoded_c = chr(ord(self.data[i]) + ord(key_c) % 256)
                encoded_chars.append(encoded_c)
            encoded_string = ''.join(encoded_chars)
            en_data = base64.b64encode(bytes(encoded_string,'utf-8')).decode()   # Save this in database
            return en_data
        except Exception as e:
            return print(e)

    def decrypt(self):
        try:
            sample_string_bytes = base64.b64decode(self.data)
            sample_string = sample_string_bytes.decode()
            encoded_chars = []
            for i in range(len(sample_string)):
                key_c = self.key[i % len(self.key)]
                encoded_c = chr((ord(sample_string[i]) - ord(key_c) + 256) % 256)
                encoded_chars.append(encoded_c)
            encoded_string = ''.join(encoded_chars)
            return encoded_string
        except Exception:
            return "Update this data again!! Something went wrong when fetching this data...."
        
if __name__ == "__main__":
    en = Crypto("549845").encrypt()
    dn = Crypto("X1pjXVha=").decrypt()
    print(en)
    print(dn)