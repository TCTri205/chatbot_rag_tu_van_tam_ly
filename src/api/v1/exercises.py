"""
Relaxation exercises API endpoint.
Provides curated breathing and mindfulness exercises.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from pydantic import BaseModel

router = APIRouter()


class Exercise(BaseModel):
    """Exercise model."""
    id: str
    title: str
    category: str
    duration_minutes: int
    description: str
    steps: List[str]
    benefits: List[str]
    icon: str = "🧘"  # Default meditation icon


# Curated exercises data
EXERCISES_DATA = [
    {
        "id": "breathing_box",
        "title": "Thở Hình Vuông (Box Breathing)",
        "category": "breathing",
        "duration_minutes": 5,
        "icon": "🫁",
        "description": "Kỹ thuật thở giúp giảm căng thẳng và lo âu, thường được sử dụng bởi quân đội Mỹ.",
        "steps": [
            "Ngồi thẳng lưng, thả lỏng vai",
            "Hít vào qua mũi đếm 4 giây",
            "Nín thở đếm 4 giây",
            "Thở ra qua miệng đếm 4 giây",
            "Nín thở đếm 4 giây",
            "Lặp lại chu kỳ 5-10 lần"
        ],
        "benefits": ["Giảm căng thẳng", "Cải thiện tập trung", "Giảm lo âu"]
    },
    {
        "id": "breathing_478",
        "title": "Thở 4-7-8",
        "category": "breathing",
        "duration_minutes": 3,
        "icon": "💨",
        "description": "Kỹ thuật thở thư giãn giúp dễ ngủ và giảm lo âu nhanh chóng.",
        "steps": [
            "Đặt đầu lưỡi phía sau răng cửa trên",
            "Thở ra hoàn toàn qua miệng, tạo âm thanh 'hú'",
            "Hít vào qua mũi đếm 4",
            "Nín thở đếm 7",
            "Thở ra qua miệng đếm 8",
            "Lặp lại 4 chu kỳ"
        ],
        "benefits": ["Giảm lo âu nhanh", "Hỗ trợ giấc ngủ", "Thư giãn sâu"]
    },
    {
        "id": "mindfulness_body_scan",
        "title": "Quét Cơ Thể (Body Scan)",
        "category": "mindfulness",
        "duration_minutes": 10,
        "icon": "🧘",
        "description": "Kỹ thuật mindfulness giúp nhận thức cơ thể và giảm căng thẳng.",
        "steps": [
            "Nằm hoặc ngồi thoải mái",
            "Nhắm mắt, tập trung vào hơi thở",
            "Chú ý đến bàn chân: cảm giác, nhiệt độ",
            "Di chuyển lên cẳng chân, đùi",
            "Quét qua bụng, ngực, vai",
            "Chú ý đến cánh tay, bàn tay",
            "Kết thúc ở đầu, mặt",
            "Thả lỏng các vùng căng thẳng"
        ],
        "benefits": ["Tăng nhận thức cơ thể", "Giảm căng thẳng cơ", "Cải thiện giấc ngủ"]
    },
    {
        "id": "breathing_diaphragmatic",
        "title": "Thở Bụng (Diaphragmatic Breathing)",
        "category": "breathing",
        "duration_minutes": 5,
        "icon": "🌬️",
        "description": "Thở sâu từ cơ hoành, giúp cung cấp oxy tốt hơn và giảm stress.",
        "steps": [
            "Nằm ngửa hoặc ngồi thoải mái",
            "Đặt một tay lên ngực, một tay lên bụng",
            "Hít vào qua mũi, để bụng nở ra (tay trên bụng di chuyển)",
            "Tay trên ngực gần như không động",
            "Thở ra chậm qua miệng, bụng xẹp xuống",
            "Lặp lại 5-10 phút"
        ],
        "benefits": ["Giảm nhịp tim", "Hạ huyết áp", "Giảm stress hiệu quả"]
    },
    {
        "id": "mindfulness_5_senses",
        "title": "5-4-3-2-1 (Kỹ thuật 5 Giác quan)",
        "category": "mindfulness",
        "duration_minutes": 5,
        "icon": "🖐️",
        "description": "Kỹ thuật grounding giúp trở về hiện tại khi lo âu hoặc hoảng loạn.",
        "steps": [
            "Nhận biết 5 thứ bạn THẤY xung quanh",
            "Nhận biết 4 thứ bạn có thể CHẠM vào",
            "Nhận biết 3 âm thanh bạn NGHE được",
            "Nhận biết 2 mùi bạn NGỬI được",
            "Nhận biết 1 vị bạn NẾM được",
            "Thở sâu và thả lỏng"
        ],
        "benefits": ["Giảm hoảng loạn", "Trở về hiện tại", "Giảm lo âu cấp tính"]
    },
    {
        "id": "mindfulness_gratitude",
        "title": "Thiền Biết Ơn",
        "category": "mindfulness",
        "duration_minutes": 5,
        "icon": "🙏",
        "description": "Tập trung vào những điều tích cực để cải thiện tâm trạng.",
        "steps": [
            "Ngồi thoải mái, nhắm mắt",
            "Thở sâu 3 lần",
            "Nghĩ về 3 điều bạn biết ơn hôm nay",
            "Cảm nhận cảm giác biết ơn trong lòng",
            "Mỉm cười nhẹ",
            "Thở sâu và mở mắt"
        ],
        "benefits": ["Tăng cảm xúc tích cực", "Giảm trầm cảm", "Cải thiện tâm trạng"]
    },
    {
        "id": "progressive_relaxation",
        "title": "Thư Giãn Cơ Tiến Triển (PMR)",
        "category": "relaxation",
        "duration_minutes": 15,
        "icon": "💆",
        "description": "Căng và thả lỏng các nhóm cơ để giải tỏa căng thẳng.",
        "steps": [
            "Nằm hoặc ngồi thoải mái",
            "Bắt đầu từ bàn chân: căng cứng 5 giây",
            "Thả lỏng hoàn toàn, cảm nhận sự khác biệt",
            "Di chuyển lên: cẳng chân, đùi, mông",
            "Tiếp tục: bụng, ngực, tay",
            "Vai, cổ, mặt",
            "Nghỉ ngơi 2-3 phút sau khi hoàn thành"
        ],
        "benefits": ["Giải tỏa căng thẳng cơ", "Cải thiện giấc ngủ", "Giảm đau mãn tính"]
    },
    {
        "id": "breathing_alternate_nostril",
        "title": "Thở Luân Phiên Mũi (Nadi Shodhana)",
        "category": "breathing",
        "duration_minutes": 5,
        "icon": "👃",
        "description": "Kỹ thuật yoga cân bằng năng lượng và làm dịu thần kinh.",
        "steps": [
            "Ngồi thẳng lưng, thả lỏng",
            "Dùng ngón cái phải bịt lỗ mũi phải",
            "Hít vào qua lỗ mũi trái",
            "Bịt lỗ mũi trái bằng ngón áp út, mở mũi phải",
            "Thở ra qua mũi phải",
            "Hít vào qua mũi phải",
            "Bịt mũi phải, thở ra qua mũi trái",
            "Lặp lại 5-10 chu kỳ"
        ],
        "benefits": ["Cân bằng tâm trí", "Giảm stress", "Tăng tập trung"]
    }
]


@router.get("/", response_model=List[Exercise])
async def get_exercises(category: str = None):
    """
    Get relaxation exercises.
    
    Args:
        category: Optional filter by category (breathing, mindfulness, relaxation)
        
    Returns:
        List of exercises
    """
    exercises = EXERCISES_DATA
    
    if category:
        exercises = [ex for ex in exercises if ex['category'] == category.lower()]
    
    return exercises


# CRITICAL: /categories MUST come BEFORE /{exercise_id}
# Otherwise FastAPI matches 'categories' as an exercise_id
@router.get("/categories")
async def get_categories():
    """
    Get available exercise categories.
    
    Returns:
        List of categories with counts
    """
    categories = {}
    for ex in EXERCISES_DATA:
        cat = ex['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    return {
        "categories": [
            {"name": cat, "count": count, "label": _get_category_label(cat)}
            for cat, count in categories.items()
        ]
    }


@router.get("/{exercise_id}", response_model=Exercise)
async def get_exercise(exercise_id: str):
    """
    Get a specific exercise by ID.
    
    Args:
        exercise_id: ID of the exercise
        
    Returns:
        Exercise details
        
    Raises:
        HTTPException 404: Exercise not found
    """
    for ex in EXERCISES_DATA:
        if ex['id'] == exercise_id:
            return ex
    raise HTTPException(
        status_code=404,
        detail=f"Exercise '{exercise_id}' not found"
    )


def _get_category_label(category: str) -> str:
    """Get Vietnamese label for category."""
    labels = {
        "breathing": "Hơi Thở",
        "mindfulness": "Chánh Niệm",
        "relaxation": "Thư Giãn"
    }
    return labels.get(category, category)

