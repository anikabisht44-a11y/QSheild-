"""TLS discovery module for QShield (P2)."""

import socket
import ssl
from datetime import datetime
from typing import Optional, Tuple

try:
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
except ImportError:
    x509 = None
    default_backend = None


ETHICS_NOTE = "Only test hosts you own or that are publicly intended to be reached. This tool performs a normal TLS handshake and nothing else."


def check_tls(hostname: str, timeout: int = 5, allow_untrusted: bool = False) -> dict:
    """Perform TLS handshake and extract certificate information.
    
    Args:
        hostname: The hostname to connect to
        timeout: Connection timeout in seconds
        allow_untrusted: Whether to allow untrusted certificates (localhost only)
    
    Returns:
        Dictionary with TLS version, cipher suite, and certificate info
    """
    if x509 is None or default_backend is None:
        return {
            "success": False,
            "error": "cryptography package not installed. Install with: pip install cryptography",
        }
    
    try:
        # Create socket
        sock = socket.create_connection((hostname, 443), timeout=timeout)
        
        # Wrap with SSL
        context = ssl.create_default_context()
        
        if allow_untrusted and hostname in ["localhost", "127.0.0.1"]:
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        
        ssl_sock = context.wrap_socket(sock, server_hostname=hostname)
        
        # Get negotiated TLS version and cipher
        tls_version = ssl_sock.version()
        cipher_suite = ssl_sock.cipher()
        
        # Get certificate
        cert_der = ssl_sock.getpeercert(binary=True)
        cert = x509.load_der_x509_certificate(cert_der, default_backend())
        
        # Extract public key info
        public_key = cert.public_key()
        key_type = type(public_key).__name__
        
        key_info = {"type": key_type}
        
        if key_type == "RSAPublicKey":
            key_info["key_size"] = public_key.key_size
        elif key_type in ["EllipticCurvePublicKey", "DSAPublicKey"]:
            # Try to get curve name
            try:
                curve_name = public_key.curve.name
                key_info["curve"] = curve_name
            except AttributeError:
                key_info["curve"] = "unknown"
        
        ssl_sock.close()
        sock.close()
        
        return {
            "success": True,
            "tls_version": tls_version,
            "cipher_suite": cipher_suite[0] if cipher_suite else "unknown",
            "public_key": key_info,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    
    except socket.timeout:
        return {
            "success": False,
            "error": f"Connection timeout after {timeout} seconds",
        }
    except socket.gaierror as e:
        return {
            "success": False,
            "error": f"DNS error: {str(e)}",
        }
    except ssl.SSLCertVerificationError as e:
        return {
            "success": False,
            "error": f"Certificate verification error: {str(e)}",
        }
    except ssl.SSLError as e:
        return {
            "success": False,
            "error": f"SSL error: {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
        }


def map_to_algorithm(tls_result: dict) -> Optional[str]:
    """Map TLS certificate public key to algorithm value per Section 10.
    
    Returns None if mapping is not possible.
    """
    if not tls_result.get("success"):
        return None
    
    public_key = tls_result.get("public_key", {})
    key_type = public_key.get("type")
    
    if key_type == "RSAPublicKey":
        key_size = public_key.get("key_size")
        if key_size == 2048:
            return "RSA-2048"
        elif key_size == 3072:
            return "RSA-3072"
        elif key_size == 4096:
            return "RSA-4096"
    
    elif key_type == "EllipticCurvePublicKey":
        curve = public_key.get("curve", "")
        if "secp256r1" in curve or "P-256" in curve:
            return "ECC P-256"
        elif "secp384r1" in curve or "P-384" in curve:
            return "ECC P-384"
    
    # Cannot map - return None to keep manual entry
    return None


def format_tls_result(tls_result: dict) -> str:
    """Format TLS result for display."""
    if not tls_result.get("success"):
        return f"Error: {tls_result.get('error', 'Unknown error')}"
    
    lines = []
    lines.append(f"TLS Version: {tls_result.get('tls_version')}")
    lines.append(f"Cipher Suite: {tls_result.get('cipher_suite')}")
    
    public_key = tls_result.get("public_key", {})
    key_type = public_key.get("type")
    
    if key_type == "RSAPublicKey":
        lines.append(f"Public Key: RSA {public_key.get('key_size')} bits")
    elif key_type == "EllipticCurvePublicKey":
        lines.append(f"Public Key: Elliptic Curve ({public_key.get('curve', 'unknown')})")
    else:
        lines.append(f"Public Key: {key_type}")
    
    lines.append(f"Checked on: {tls_result.get('date')}")
    lines.append("")
    lines.append("Post-quantum key exchange: not checked.")
    
    return "\n".join(lines)
