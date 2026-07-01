"""
End-to-end verification for Phase 1 (Hybrid Engine) and Phase 2 (Homepage).

Run from the project root:
    python -m test.verify_phases
"""

import os
import sys

# Ensure .env is loaded for TMDB API key
from dotenv import load_dotenv
load_dotenv()


def divider(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_config():
    divider("1. Config Module")
    from recommendation.config import (
        HYBRID_WEIGHT_CONTENT,
        HYBRID_WEIGHT_COLLABORATIVE,
        HYBRID_WEIGHT_POPULARITY,
        HOMEPAGE_SECTION_SIZE,
        HOMEPAGE_GENRES,
    )

    total = HYBRID_WEIGHT_CONTENT + HYBRID_WEIGHT_COLLABORATIVE + HYBRID_WEIGHT_POPULARITY
    assert abs(total - 1.0) < 1e-9, f"Hybrid weights must sum to 1.0, got {total}"
    print(f"  Hybrid weights: content={HYBRID_WEIGHT_CONTENT}, "
          f"collab={HYBRID_WEIGHT_COLLABORATIVE}, "
          f"pop={HYBRID_WEIGHT_POPULARITY} (sum={total})")
    print(f"  Homepage section size: {HOMEPAGE_SECTION_SIZE}")
    print(f"  Genre sections: {HOMEPAGE_GENRES}")
    print("  ✅ Config OK")


def test_schemas():
    divider("2. Schemas")
    from recommendation.common.schemas import (
        Recommendation, Scores, Explanation, HomepageSection,
    )

    rec = Recommendation(
        tmdbId=27205,
        title="Inception",
        poster="https://example.com/poster.jpg",
        scores=Scores(content=0.9),
        explanation=Explanation(engine="test", reasons=["Test reason"]),
        source="test",
    )
    print(f"  Recommendation: {rec.title} (tmdb={rec.tmdbId})")

    section = HomepageSection(
        section_id="test",
        title="Test Section",
        section_type="editorial",
        movies=[rec],
    )
    print(f"  HomepageSection: {section.title} ({len(section.movies)} movies)")
    print("  ✅ Schemas OK")


def test_normalizer():
    divider("3. Normalizer")
    from recommendation.hybrid.normalizer import min_max_normalize, normalize_scores
    from recommendation.common.schemas import Recommendation, Scores, Explanation

    # Unit test min_max_normalize
    assert min_max_normalize([]) == []
    assert min_max_normalize([5.0, 5.0]) == [1.0, 1.0]
    assert min_max_normalize([0.0, 1.0]) == [0.0, 1.0]
    assert min_max_normalize([2.0, 4.0, 6.0]) == [0.0, 0.5, 1.0]
    print("  min_max_normalize: ✅")

    # Unit test normalize_scores
    recs = [
        Recommendation(tmdbId=1, title="A", poster="", scores=Scores(content=0.2),
                       explanation=Explanation(engine="t"), source="t"),
        Recommendation(tmdbId=2, title="B", poster="", scores=Scores(content=0.8),
                       explanation=Explanation(engine="t"), source="t"),
        Recommendation(tmdbId=3, title="C", poster="", scores=Scores(content=None),
                       explanation=Explanation(engine="t"), source="t"),
    ]
    norm = normalize_scores(recs, "content")
    assert norm[1] == 0.0  # min
    assert norm[2] == 1.0  # max
    assert 3 not in norm   # None skipped
    print(f"  normalize_scores: {norm} ✅")


def test_merger():
    divider("4. Merger")
    from recommendation.hybrid.merger import merge_recommendations
    from recommendation.common.schemas import Recommendation, Scores, Explanation

    content = [
        Recommendation(tmdbId=100, title="Movie A", poster="p1",
                       scores=Scores(content=0.9, popularity=0.7),
                       explanation=Explanation(engine="content", reasons=["Genre match"]),
                       source="content"),
    ]
    collab = [
        Recommendation(tmdbId=100, title="Movie A", poster="p2",
                       scores=Scores(collaborative=4.2),
                       explanation=Explanation(engine="collab", reasons=["Users liked"]),
                       source="collaborative"),
        Recommendation(tmdbId=200, title="Movie B", poster="p3",
                       scores=Scores(collaborative=3.8),
                       explanation=Explanation(engine="collab", reasons=["Predicted 3.8"]),
                       source="collaborative"),
    ]

    merged = merge_recommendations(content, collab)
    print(f"  Merged {len(content)} content + {len(collab)} collab → {len(merged)} results")

    movie_a = next(m for m in merged if m.tmdbId == 100)
    assert movie_a.scores.content == 0.9, "Content score preserved"
    assert movie_a.scores.collaborative == 4.2, "Collab score merged"
    assert movie_a.scores.popularity == 0.7, "Popularity preserved from content"
    assert movie_a.poster == "p1", "Content poster takes priority"
    assert "Genre match" in movie_a.explanation.reasons
    assert "Users liked" in movie_a.explanation.reasons
    assert movie_a.source == "hybrid"
    print(f"  Movie A merged: content={movie_a.scores.content}, "
          f"collab={movie_a.scores.collaborative}, source={movie_a.source}")

    movie_b = next(m for m in merged if m.tmdbId == 200)
    assert movie_b.scores.collaborative == 3.8
    assert movie_b.source == "hybrid"
    print(f"  Movie B: collab-only, source={movie_b.source}")
    print("  ✅ Merger OK")


def test_ranker():
    divider("5. Ranker")
    from recommendation.hybrid.ranker import rank_recommendations
    from recommendation.common.schemas import Recommendation, Scores, Explanation

    recs = [
        Recommendation(tmdbId=1, title="Low", poster="",
                       scores=Scores(content=0.3, collaborative=0.2, popularity=0.1),
                       explanation=Explanation(engine="t"), source="t"),
        Recommendation(tmdbId=2, title="High", poster="",
                       scores=Scores(content=0.9, collaborative=0.8, popularity=0.9),
                       explanation=Explanation(engine="t"), source="t"),
        Recommendation(tmdbId=3, title="Mid", poster="",
                       scores=Scores(content=0.5, collaborative=0.5, popularity=0.5),
                       explanation=Explanation(engine="t"), source="t"),
    ]

    norm_c = {1: 0.0, 2: 1.0, 3: 0.5}
    norm_cf = {1: 0.0, 2: 1.0, 3: 0.5}
    norm_p = {1: 0.0, 2: 1.0, 3: 0.5}

    ranked = rank_recommendations(recs, norm_c, norm_cf, norm_p, top_n=2)

    assert len(ranked) == 2
    assert ranked[0].tmdbId == 2, "Highest hybrid score first"
    assert ranked[1].tmdbId == 3, "Mid score second"
    assert ranked[0].scores.hybrid is not None
    print(f"  Ranked: {[(r.title, f'{r.scores.hybrid:.2f}') for r in ranked]}")
    print("  ✅ Ranker OK")


def test_deduplicator():
    divider("6. Deduplicator")
    from recommendation.homepage.deduplicator import deduplicate_sections
    from recommendation.common.schemas import (
        Recommendation, Scores, Explanation, HomepageSection,
    )

    def make_rec(tmdb_id, title):
        return Recommendation(
            tmdbId=tmdb_id, title=title, poster="",
            scores=Scores(), explanation=Explanation(engine="t"),
            source="t",
        )

    sections = [
        HomepageSection(
            section_id="s1", title="Section 1", section_type="personalized",
            movies=[make_rec(1, "A"), make_rec(2, "B")],
        ),
        HomepageSection(
            section_id="s2", title="Section 2", section_type="trending",
            movies=[make_rec(2, "B"), make_rec(3, "C")],  # B is duplicate
        ),
        HomepageSection(
            section_id="s3", title="Section 3", section_type="genre",
            movies=[make_rec(1, "A"), make_rec(2, "B")],  # all duplicates
        ),
    ]

    result = deduplicate_sections(sections)

    assert len(result) == 2, f"Section 3 should be dropped (empty), got {len(result)}"
    assert len(result[0].movies) == 2  # Section 1 keeps both
    assert len(result[1].movies) == 1  # Section 2 keeps only C
    assert result[1].movies[0].tmdbId == 3
    print(f"  Input: 3 sections (2+2+2 movies)")
    print(f"  Output: {len(result)} sections "
          f"({'+'.join(str(len(s.movies)) for s in result)} movies)")
    print("  ✅ Deduplicator OK")


def test_content_recommend():
    divider("7. Content-Based Recommender")
    from recommendation.content_based.recommender import recommend

    recs = recommend(["Avatar"], top_n=3)
    print(f"  'Avatar' → {len(recs)} recommendations:")
    for r in recs:
        print(f"    • {r.title} (content={r.scores.content:.2f}, "
              f"source={r.source})")
    assert len(recs) > 0, "Should return at least 1 recommendation"
    assert all(r.source == "content" for r in recs)
    print("  ✅ Content Recommender OK")


def test_collaborative_recommend():
    divider("8. Collaborative Recommender")
    from recommendation.collaborative.recommender import recommend

    recs = recommend(user_id=1, top_n=3)
    print(f"  User 1 → {len(recs)} recommendations:")
    for r in recs:
        print(f"    • {r.title} (collab={r.scores.collaborative:.2f}, "
              f"source={r.source})")
    assert len(recs) > 0, "Should return at least 1 recommendation"
    assert all(r.source == "collaborative" for r in recs)
    print("  ✅ Collaborative Recommender OK")


def test_hybrid_recommend():
    divider("9. Hybrid Recommender (full pipeline)")
    from recommendation.hybrid.recommender import recommend

    # Full hybrid: user + liked movies
    recs = recommend(user_id=1, liked_movies=["Avatar"], top_n=5)
    print(f"  Hybrid (user=1, liked=['Avatar']) → {len(recs)} recs:")
    for r in recs:
        print(f"    • {r.title} | hybrid={r.scores.hybrid:.3f} "
              f"c={r.scores.content} cf={r.scores.collaborative} "
              f"p={r.scores.popularity}")
    assert len(recs) > 0
    # Verify hybrid scores are set and sorted descending
    hybrid_scores = [r.scores.hybrid for r in recs]
    assert all(s is not None for s in hybrid_scores)
    assert hybrid_scores == sorted(hybrid_scores, reverse=True), \
        "Should be sorted by hybrid score descending"
    print("  ✅ Hybrid Recommender OK")

    # Cold start: content only
    divider("9b. Cold Start (content only)")
    recs_cold = recommend(user_id=None, liked_movies=["The Dark Knight"], top_n=3)
    print(f"  Content-only cold start → {len(recs_cold)} recs:")
    for r in recs_cold:
        print(f"    • {r.title} | hybrid={r.scores.hybrid:.3f}")
    assert len(recs_cold) > 0
    print("  ✅ Cold Start OK")


def test_recommendation_service():
    divider("10. RecommendationService")
    from recommendation.services.recommendation_service import RecommendationService

    svc = RecommendationService()

    # Search
    results = svc.search("dark kni", max_results=5)
    print(f"  search('dark kni') → {len(results)} results:")
    for r in results:
        print(f"    • {r['title']} (tmdb={r['tmdbId']})")
    assert len(results) > 0
    print("  ✅ Search OK")

    # recommend_similar
    similar = svc.recommend_similar(["Avatar"], top_n=3)
    print(f"\n  recommend_similar(['Avatar']) → {len(similar)} results")
    assert len(similar) > 0
    print("  ✅ recommend_similar OK")

    # recommend_for_user
    user_recs = svc.recommend_for_user(
        user_id=1, liked_movies=["Avatar"], top_n=3
    )
    print(f"  recommend_for_user(1, ['Avatar']) → {len(user_recs)} results")
    assert len(user_recs) > 0
    print("  ✅ recommend_for_user OK")


def test_homepage():
    divider("11. Homepage (Phase 2)")
    from recommendation.homepage.orchestrator import HomepageOrchestrator

    orch = HomepageOrchestrator()

    # Anonymous user homepage
    print("  Building anonymous homepage...")
    sections = orch.get_homepage(user_id=None, liked_movies=None)
    print(f"  Anonymous → {len(sections)} sections:")
    total_movies = 0
    for s in sections:
        print(f"    • [{s.section_type:>13}] {s.title} ({len(s.movies)} movies)")
        total_movies += len(s.movies)

    assert len(sections) > 0, "Should have at least universal sections"
    print(f"  Total movies: {total_movies}")

    # Check no duplicates across sections
    all_tmdb_ids = []
    for s in sections:
        for m in s.movies:
            all_tmdb_ids.append(m.tmdbId)
    assert len(all_tmdb_ids) == len(set(all_tmdb_ids)), \
        "Duplicate movies found across sections!"
    print("  ✅ No duplicates across sections")

    # Personalised user homepage
    print(f"\n  Building personalised homepage (user=1)...")
    p_sections = orch.get_homepage(user_id=1, liked_movies=["Avatar", "Inception"])
    print(f"  Personalised → {len(p_sections)} sections:")
    for s in p_sections:
        print(f"    • [{s.section_type:>13}] {s.title} ({len(s.movies)} movies)")

    # Should have personalized sections
    section_types = {s.section_type for s in p_sections}
    assert "personalized" in section_types, "Should have personalized sections"
    print("  ✅ Homepage OK")


if __name__ == "__main__":
    tests = [
        test_config,
        test_schemas,
        test_normalizer,
        test_merger,
        test_ranker,
        test_deduplicator,
        test_content_recommend,
        test_collaborative_recommend,
        test_hybrid_recommend,
        test_recommendation_service,
        test_homepage,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"\n  ❌ FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    divider("RESULTS")
    print(f"  Passed: {passed}/{len(tests)}")
    print(f"  Failed: {failed}/{len(tests)}")
    if failed > 0:
        sys.exit(1)
    else:
        print("\n  🎉 All tests passed!")
