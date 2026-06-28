import os
import urllib.request

SCREENS = {
    "login": {
        "title": "Sign In",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLscjtAJNytwcLDDT1ugXhaoIGS_y83c-OmoUQ3jxUzNPlEvgK01llHY_gcGMV3UbLpZjN1Sb16R28ffwW41rbX-uAybqa6riCTYOlkrXsWPPZJO4R9torXMfUZw4zRwnyEa-dyB03gVlEvoMJ85RJRPhHRnrY56C4p9giPVmLwuKgIqVKxiJYkeLocqRWxQqtMJFJ1iIz4rHtzvpj9Pcibs1_GjnphISSh1CUmxrBrKlZkv2QkVX4YUFg6G",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzg0MzA5N2EwOGFiNjQ5OGY4YTBiMjQyNTJlYTZjMzg1EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "register": {
        "title": "Join Community Hero",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLsuQNGhvZ3Q8y9N0dceGicmrNR0lCEsNYQ1pfNxsTwFdbdG9nwsvHT38-PdG4DNla-ojCOrHRO70HO_3JgcaTHwj0LX3pHOX0j-3vKMLSYYm5xvNPLG6517boq4E2kNyPV7g3UNTk8ddw9l68qgIBzzg0DOjwmv0HYRMYXtn3hinWPoPm8zdEkdxVi8cK9Q-VXLOc2tds1xgXjTd5RdPiofmaQU3_SkaxcafgsMEIFHU4vGQf1BgIQgFk1W",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2RiZjg5NmExMDNiOTRmNmE5OWZkMTI1NDdiZmRkZTI5EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "user_directory": {
        "title": "User Directory - Admin Console",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLvonhjK9MWzJLPKVeeTUZERXvUt4ipkQV6xYBRE_LlEL4dEeRkcdD0yFCQafs8XxpsdLeOaJYcrPvVtuNCmCHMMxjqZKjekAyq0NCsTnGzO7P-d8msGSsNcFqN4fZIT12Z5JZK0wni83jZystWoERIXoeeMgE2WPPYcAaiFDiTlh8rgeVR5kMalpFa5UI7cQf7piY8t-LoRYc4Uw6iWW9Z9KdtRSBRXvADbCoQm8V-Mj8vbkKTPeDhrGXI",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzAzZDNkYmEzODczMTRhOTg4ODJmODdmNjFhZDQ1MmIxEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "department_management": {
        "title": "Department Management - Admin Console",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLuxFHhqrTv-KR88XDWSosMR7-wFjEvT-0vi-su0tXk-J3_0ozaQthrNuQjphh7xUBfywR_br9Uwjts6TiWsb60WGWYdqrebpHgeMg5ilX6qQTekvm86RAvivhgnJwnbvy1hzVv-rzbKyFjtu5X6kbhWMuuSftKnY2qnZiEdaUuqB07Df_CwXm7P1mHYPgKVPyXJoCSOnyNOIDxMmWBW_8KOgOqicNelmATUqkukcsqSD1EUf4dh67bQVUI",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzY2MTI5NTZjZDNiODRmNGJiYWNlYzEwNDI0NWEyZThiEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "my_reported_issues": {
        "title": "My Reported Issues - Citizen Portal",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLu_Uzwcx0knva9u7Rhh4bo2oRYoEF1Cq4W4hSJTCCGr0HbtSdSO740skGRI2QnFWsThEAQybuBGAJdkajJaCkXWFXJOEGyqCcBh2Bc0OK02gGo6P3ZoQNupmW7aoRIt3HpEGMslJzmRIl6FbR3XnUHT4vv-a8EvSeAoirDPDZH7MSxPrfY7VSg092zDTr-0PXCkj8qeQ7frdwihF4Hpb4xNUrZBQTA_riPID7he4-ggn4Gu-7hBUM-U2vhF",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzJmOWFiYzBjNjkyYzQ2MzE5OGRiZThjMGRlZWVhNTM1EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "admin_console": {
        "title": "Admin Console - Municipal Control",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLseY7EYtb-r7WJ2NE2Mf4wqu2ptaJaSvboHI2LrD-ExeDBq-HAfiZx9-w1Dsbk0jknNwX32mO1XNjfhyi-lEJelPtCo2mO07quN5mwizVnPoS8UcBXFHIEK_bij1PeRznBaKRoSX9FZCLIjpLNZE8G2luEvdqXgiWytC_EZGvSzuCvlwEHNgfUh5kVB3vLJpwDw02imTCDJW5G45VVyEc2hg__7A8BHudwVIDZV10q9ZS8jsIO4IEOk2Any",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzc3YmI1MjBlOTA4ZDRmYmE4Y2FkMDZiYmM5NmE2YTA3EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "public_dashboard": {
        "title": "Public Impact Dashboard",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLtspR6uDhizmsFXQe_5qb0O7dAjY1G-rbD7Rut62obsH3H8u3GGgW4r35WvM6Fq88nqWtbqWgezw2ddRibLog9keeQzPf0uzkfKv8ivrZPnlspTLf5VXLVOalWl9sHstajMwDYO8n3M6z4VWxnnNcT5RbeDfFN-SHSV4XzXPVr07iHBllVEQh8WYNFvuUibuegb-hci_PG3DvcU1VI0g8M-hvAkuWhcECyjfKqQaVLNWIesaHjnicZx7Rv-",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzQ1NTRiZDQ2MjMyODQwOTM4MTA0NzA4NzkwYTJmYTY0EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "my_profile": {
        "title": "My Profile",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLvl3Sqpv8gjAozsSF6kW-Ij_P8HwdioevJXBRSmpDul-kadkNSpKe7kUCm3zp1GUUoF4C-AanFx1-z3Us-Yi5mgfXhf8oEM3IJThHe9KyrNtojpjYse_wRv-7WAERYo6CHGAFkuCJGoby4lmJntT5epqBgG5p5W6Pvkmw2dIvyGrPsmhdZPWc-kz5aOKDA7WztHD9bzcgM5NDXcWjo73UJZQPGqfAZmbmZ2L7WUKp6_z0RM58WeJah9pch0",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2M0ZmI4NWU5Yjg0MDQ5YzU5NDliMjVkOTA4YTdmYTA5EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "report_issue": {
        "title": "Report a Civic Issue",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLtfmaYshenaxg_iYeATYcqmsqmOgoG78RT11ON-LqEGkH5QSX3BZfBVDHWNeTT03nG7_ElmMQj6Bu6PW0Fv1g-ItdtAEoqOM7OngqFiZIDm-IXFc_MTuhWL7xqidEdehszNYjiRROpiB4_hU6qk_PFCeWpTouZ-h7r3OepOvHW7y2tVS2ZCZGjouvQjDaaIU36RHtFL8vx_oNVxMIyCyuduhw8MGtlWBF44y4g5MCrJ3-UABRL3mt7lrShI",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2Q2NTZiMTNkYjA0YjQ5ZWM4YjgyN2RhYjMwYWQ5MTEzEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "leaderboard": {
        "title": "Leaderboard",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLtsNjfEOmACf3Ml27idtJh_lZHBaXaUZ8H0TR9YZ85ybASPiOtjwB5-SmqgCIv9RVMEe9eDaNnTKXMSm_C7PfV2dNmj2tOh_jS4FzUKxgSh8OmOuit4ADjePIaBlA3VZiXOvQBZFuthcpDmFA4YUsZvoNbHru6AyYy6GQkJT6reSwJy4U546eo-PBc8ZofJzIplGS4QnBip_FL71fZ5ivq6_9RfSy1LwbfMvg1SjI2yWqCLBiBUqwNLlOI",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzM4MjQ1ZDZkNDA0NTQyNWU5ZmM2MTIxNDE3MzcxYmI4EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "explore_map": {
        "title": "Explore Map",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLslnrAU-R0NWKKE219dE8y5ioxChUyEnlmAAxDONFAmac60opVx52kJk902ITl0ddFszsE-QoueZIgs6kYhzCAUU2EGbFtK5Bs7RZA5qs63QdzK_oSYfn0nkN_ljAbM3WU3uI8GsQkhY9lD5EWFKNSdEJts_c9KdvJDlVVFkSpIyfGaiKAvhfkHXjAZggXVn7zbikeLuaMk2PZl60LBxKYG8ZWYGXAlD2nkTePHpZZ5O_OaWh0Hbf530FXy",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2Y0ZTZjYjI0ZjFmZTQ1NmU5NTlkZmU0YTBiMDFiYTAyEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "manage_issues": {
        "title": "Manage Issues - Admin Console",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLuAyfQusOGrWSsR7HLnz_ysObV2cpE2_fMVT3-4epUwC2lAU0u_otQZNM3fG4Lwcf_45gIBrIUB5pOgEWIbdTajFqsxsFN79vmCknwIq4LoovnAeE_t4wZanRLiIHFbDF6wsSHVv4NJBww6q5Lyw2tLhmvyBrlmLdarmAJxAFQuzRj6FEUtb12CibkvF1Vu9FpNn20MCLDnO8RO7AfQIQ0xoncV8u5bUlFI8uc4OQa6tkWwC6h8oE3iDTZ-",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzM4NjVkMWRkODU4MzQ0YTk5MTUzNjAyYWIyMDViZjE2EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "municipal_analytics": {
        "title": "Municipal Analytics - Admin Console",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLtk14Lk1ehGfKwzsT8taeE0SUefp5pi-iuQrvZuLrsITEUaS3l17xFQeaeWvvg_GlcsnZ-vU8udyiDcqHAqmeqj4cm-5NPn6f2Qof21mogXZ2UewksmhxHKCddv0466dG3KdzLhg7abWg_zdt6HVmobyvx5nqsGphkEblPa_PyXMDjbd9f8jatZuwEe6SzqffcdgbBVQo4Gl8aQyYT5OTz-pVCcKSDejJ9RPX0u5CDfGDcCJCeW9cvj7nwC",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzk0MDhjM2JjY2M2OTRjYjI5YzA1MjFlMDQwMTczZWU4EgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "citizen_portal": {
        "title": "Citizen Portal",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLu6VAcKRlatRwlfOlwmRCU85Ew5G5ywLGQv8_2t1s-kpKhoZkNMbfdS7Hfry5pN7q6cU0B9y5OO5BVSQA274CwvI0XxGaVdUP5arm08eRtbiJvUT0_nGZxQJZ-ffRowf2kkkU6iPGkLhYSWAMgFxBO6Xl7dsXot6V-6ouAPn5WK3Bi1w6zPk6WTZ_19XCXpf2ZY0EQM5nY0FtbCXOH8VjkWkJ5qcZ6Cepd9tXlp-0k2cfs0ElpneYMXHRY",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sXzQ3NDAzYWIxNWU1NTQzODliZGJkZTJmYjc5ZTc4ODNiEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    },
    "issue_detail": {
        "title": "Issue Report Details",
        "screenshot": "https://lh3.googleusercontent.com/aida/AP1WRLufYMb7k_C8hWKa3jAyTvslxIzrbY_I5zwS0K14VTJHaWYrSdFZbC2qsoJQRL7Ax9mFVaYIRzV7omqkcfnP3BS5eD3EBFSiLv4fb5MLZVWdYVxCgYYfBTfiPDW8SzporNl4I4FXGUoMv29s_hgK2mCr3v6prChi-0w1HAAELXMkiuFGaQ2gOa8UUgyDsDjZdmOD2qbwTxc5biLKb7zPid9UQoI2TlgWG4MIIb919FvYVSpbBPTUAIR4PxYG",
        "html": "https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ8Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpbCiVodG1sX2U4ZWUyYjc1MTljMDRmNDNiNzk5NWMwMjEwMGRmOWIxEgsSBxDPgsW0uBUYAZIBJAoKcHJvamVjdF9pZBIWQhQxMjc3MzA3NzYzOTE2NDU2NjA0Ng&filename=&opi=89354086"
    }
}

DEST_DIR = r"f:\CN Hackathon\frontend\stitch_reference"

def main():
    os.makedirs(DEST_DIR, exist_ok=True)
    print(f"Target directory: {DEST_DIR}")
    
    # Headers to bypass potential simple bot blockings
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    urllib.request.install_opener(opener)
    
    for key, data in SCREENS.items():
        title = data["title"]
        print(f"Downloading assets for {title}...")
        
        # HTML code download
        html_dest = os.path.join(DEST_DIR, f"{key}.html")
        try:
            urllib.request.urlretrieve(data["html"], html_dest)
            print(f"  Saved HTML -> {html_dest}")
        except Exception as e:
            print(f"  Error downloading HTML for {key}: {e}")
            
        # Screenshot image download
        img_dest = os.path.join(DEST_DIR, f"{key}.png")
        try:
            urllib.request.urlretrieve(data["screenshot"], img_dest)
            print(f"  Saved PNG -> {img_dest}")
        except Exception as e:
            print(f"  Error downloading image for {key}: {e}")

if __name__ == "__main__":
    main()
