# test_tools.py
from brain import SearchTool, GuidebookTool, MemoryTool

def test_all():
    print("=== 서치 툴 ===")
    search = SearchTool().build()
    print(search.invoke("오늘 날씨 서울"))

    print("\n=== 가이드북 툴 ===")
    guidebook = GuidebookTool().build()
    print(guidebook.invoke("하루 캐릭터 설정"))

    print("\n=== 메모리 툴 ===")
    memory = MemoryTool().build()
    print(memory.invoke("저번에 한 얘기"))

if __name__ == "__main__":
    test_all()