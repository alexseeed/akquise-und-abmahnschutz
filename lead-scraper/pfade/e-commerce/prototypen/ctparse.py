"""Minimal static-ct-api data tile + RFC6962 leaf parser (stdlib only).
Extracts SAN dNSNames from (pre)certificates."""
import struct, gzip, sys, json, base64

def der_read(buf, i):
    tag = buf[i]; i += 1
    l = buf[i]; i += 1
    if l & 0x80:
        n = l & 0x7f
        l = int.from_bytes(buf[i:i+n], 'big'); i += n
    return tag, i, i + l   # tag, content start, content end

SAN_OID = bytes.fromhex('0603551d11')

def san_names(der):
    """der = TBSCertificate or Certificate DER. Return list of dNSName strings."""
    out = []
    j = der.find(SAN_OID)
    if j < 0:
        return out
    i = j + len(SAN_OID)
    # optional BOOLEAN critical
    if der[i] == 0x01:
        _, s, e = der_read(der, i); i = e
    tag, s, e = der_read(der, i)          # OCTET STRING
    if tag != 0x04:
        return out
    tag, s2, e2 = der_read(der, s)        # SEQUENCE of GeneralName
    k = s2
    while k < e2:
        tag, cs, ce = der_read(der, k)
        if tag == 0x82:
            try: out.append(der[cs:ce].decode('ascii').lower())
            except Exception: pass
        k = ce
    return out

def parse_tile(data):
    """Yield (timestamp_ms, entry_type, names) from a static-ct data tile."""
    i = 0; n = len(data)
    while i < n:
        ts, et = struct.unpack('>QH', data[i:i+10]); i += 10
        if et == 0:   # x509_entry
            l = int.from_bytes(data[i:i+3], 'big'); i += 3
            cert = data[i:i+l]; i += l
            el = int.from_bytes(data[i:i+2], 'big'); i += 2 + el   # extensions
            cl = int.from_bytes(data[i:i+2], 'big'); i += 2 + cl   # chain fingerprints
            yield ts, 'cert', san_names(cert)
        else:          # precert_entry
            i += 32   # issuer_key_hash
            l = int.from_bytes(data[i:i+3], 'big'); i += 3
            tbs = data[i:i+l]; i += l
            el = int.from_bytes(data[i:i+2], 'big'); i += 2 + el
            pl = int.from_bytes(data[i:i+3], 'big'); i += 3 + pl   # pre_certificate
            cl = int.from_bytes(data[i:i+2], 'big'); i += 2 + cl
            yield ts, 'precert', san_names(tbs)

def parse_rfc6962_entries(js):
    """get-entries JSON -> (ts, type, names)."""
    for e in js['entries']:
        leaf = base64.b64decode(e['leaf_input'])
        # MerkleTreeLeaf: version(1) leaf_type(1) TimestampedEntry
        ts, et = struct.unpack('>QH', leaf[2:12])
        p = 12
        if et == 0:
            l = int.from_bytes(leaf[p:p+3], 'big'); p += 3
            yield ts, 'cert', san_names(leaf[p:p+l])
        else:
            p += 32
            l = int.from_bytes(leaf[p:p+3], 'big'); p += 3
            yield ts, 'precert', san_names(leaf[p:p+l])
